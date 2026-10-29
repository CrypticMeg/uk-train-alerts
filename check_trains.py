"""Check configured UK train journeys and send ntfy alerts."""
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
import yaml
from dotenv import load_dotenv

BASE_URL = "https://data.rtt.io"
PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config.yaml"

load_dotenv(PROJECT_DIR / ".env")

RTT_REFRESH_TOKEN = os.environ["RTT_API_TOKEN"]
NTFY_TOPIC_URL = os.environ["NTFY_TOPIC_URL"]

WEEKDAY_NUMBERS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

NTFY_PRIORITY_MAP = {
    "low": "low",
    "normal": "default",
    "high": "high",
}


def load_config() -> dict:
    """Load and validate config.yaml."""
    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    required_keys = {"commute_days", "state_file", "alerts", "journeys"}
    missing = required_keys - config.keys()

    if missing:
        raise ValueError(f"Missing config keys: {', '.join(sorted(missing))}")

    return config


CONFIG = load_config()
STATE_FILE = PROJECT_DIR / CONFIG["state_file"]

COMMUTE_WEEKDAYS = {
    WEEKDAY_NUMBERS[day]
    for day in CONFIG["commute_days"]
}

DELAY_ALERT_MINUTES = CONFIG["alerts"]["delay_minutes"]
MAJOR_DELAY_ALERT_MINUTES = CONFIG["alerts"]["major_delay_minutes"]


# ---------- HTTP helper ----------

def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """Make an HTTP request, retrying up to three times."""
    last_error = None

    for attempt in range(3):
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            print(f"Request failed (attempt {attempt + 1}): {error}")
            time.sleep(2 ** attempt)

    raise last_error


# ---------- RTT API ----------

def get_access_token() -> str:
    """Exchange the RTT refresh token for an access token."""
    response = request_with_retry(
        "POST",
        f"{BASE_URL}/api/get_access_token",
        headers={"Authorization": f"Bearer {RTT_REFRESH_TOKEN}"},
    )
    return response.json()["token"]


def get_departures(
    origin: str,
    destination: str,
    scheduled_departure: str,
    access_token: str,
) -> dict:
    """Fetch departures around the scheduled time from RTT."""
    departure_time = datetime.strptime(scheduled_departure, "%H:%M").time()
    today = datetime.now().date()

    time_from = datetime.combine(today, departure_time) - timedelta(minutes=90)
    time_to = datetime.combine(today, departure_time) + timedelta(minutes=30)

    response = request_with_retry(
        "GET",
        f"{BASE_URL}/rtt/location",
        params={
            "code": f"gb-nr:{origin}",
            "filterTo": f"gb-nr:{destination}",
            "timeFrom": time_from.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeTo": time_to.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()


# ---------- Train status ----------

def parse_time(value: str) -> datetime:
    """Parse an ISO 8601 timestamp."""
    return datetime.fromisoformat(value)


def find_train(
    services: list,
    scheduled_departure: str,
) -> Optional[dict]:
    """Return the service departing at the scheduled time, if any."""
    for service in services:
        departure = service["temporalData"]["departure"]
        advertised = departure.get("scheduleAdvertised")

        if advertised and advertised[11:16] == scheduled_departure:
            return service

    return None


def assess_train(service: dict) -> tuple[Optional[str], str]:
    """Return a status and priority for the service."""
    departure = service["temporalData"]["departure"]

    if departure.get("isCancelled"):
        return "CANCELLED", "high"

    if service["temporalData"].get("displayAs") == "CANCELLED":
        return "CANCELLED", "high"

    advertised = departure.get("scheduleAdvertised")
    forecast = departure.get("realtimeForecast")

    if not advertised or not forecast:
        return None, "low"

    delay_minutes = int(
        (parse_time(forecast) - parse_time(advertised)).total_seconds() // 60
    )

    if delay_minutes >= MAJOR_DELAY_ALERT_MINUTES:
        return f"DELAYED by {delay_minutes} minutes", "high"

    if delay_minutes >= DELAY_ALERT_MINUTES:
        return f"DELAYED by {delay_minutes} minutes", "normal"

    return None, "low"


def describe_train(service: dict) -> str:
    """Return a short description of the service."""
    departure = service["temporalData"]["departure"]
    scheduled = departure["scheduleAdvertised"][11:16]
    destination = service["destination"][0]["location"]["description"]

    platform = service.get("locationMetadata", {}).get("platform", {})
    forecast_platform = platform.get("forecast") or platform.get("planned")

    message = f"{scheduled} to {destination}"

    if forecast_platform:
        message += f", platform {forecast_platform}"

    return message


# ---------- Alert state ----------

def load_state() -> dict:
    """Load alert state, returning an empty dict if unusable."""
    if not STATE_FILE.exists():
        return {}

    try:
        content = STATE_FILE.read_text().strip()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        print(
            "Warning: state file was empty or invalid; "
            "resetting alert state."
        )
        return {}


def save_state(state: dict) -> None:
    """Write alert state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def should_send_alert(service_id: str, status: str, state: dict) -> bool:
    """Return True if this alert has not yet been sent today."""
    key = f"{service_id}:{status}"
    today = datetime.now(timezone.utc).date().isoformat()

    if state.get(key) == today:
        return False

    state[key] = today
    return True


# ---------- Notifications ----------

def send_notification(
    title: str,
    message: str,
    priority: str = "high",
) -> None:
    """Send a notification through ntfy."""
    ntfy_priority = NTFY_PRIORITY_MAP.get(priority, "default")

    response = request_with_retry(
        "POST",
        NTFY_TOPIC_URL,
        data=message.encode(),
        headers={
            "Title": title,
            "Priority": ntfy_priority,
            "Tags": "train,warning",
        },
    )

    print(f"ntfy notification sent: {response.status_code}")


# ---------- Main ----------

def main() -> None:
    """Check active journeys and send any alerts."""
    today_weekday = datetime.now().weekday()

    if today_weekday not in COMMUTE_WEEKDAYS:
        print("Not a configured commute day.")
        return

    now_hm = datetime.now().strftime("%H:%M")

    active_journeys = [
        journey
        for journey in CONFIG["journeys"]
        if journey["check_from"] <= now_hm <= journey["check_to"]
    ]

    if not active_journeys:
        print("Outside configured commute checking windows.")
        return

    access_token = get_access_token()
    state = load_state()

    for journey in active_journeys:
        print(f"Checking {journey['label']}...")

        data = get_departures(
            journey["origin"],
            journey["destination"],
            journey["scheduled_departure"],
            access_token,
        )

        service = find_train(
            data.get("services", []),
            journey["scheduled_departure"],
        )

        if service is None:
            print(
                f"Could not find {journey['scheduled_departure']} "
                f"from {journey['origin']} to {journey['destination']}."
            )
            continue

        service_id = service["scheduleMetadata"]["uniqueIdentity"]
        status, priority = assess_train(service)

        if status is None:
            print(f"{describe_train(service)}: running normally.")
            continue

        if not should_send_alert(service_id, status, state):
            print(f"Alert already sent: {describe_train(service)} — {status}")
            continue

        reasons = service.get("reasons") or []
        reason = ""
        if reasons:
            reason = f" Reason: {reasons[0].get('shortText', '')}"

        message = f"{describe_train(service)} is {status}.{reason}"

        send_notification(
            title=f"{journey['label']}: {status}",
            message=message,
            priority=priority,
        )

        print(f"Notification sent: {message}")

    save_state(state)


if __name__ == "__main__":
    main()
