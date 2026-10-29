"""Smoke tests for check_trains.

Network calls are faked at the `requests.request` level, and the clock is
frozen, so these exercise main() end to end against config.example.yaml
(Tue/Fri, ABC -> XYZ, 08:00 departure, checked 07:15-08:45, delay alerts at
5 minutes and high-priority delay alerts at 10).
"""
import json
from datetime import datetime, timezone

import pytest

TUESDAY_IN_WINDOW = datetime(2026, 10, 27, 7, 30)
WEDNESDAY_IN_WINDOW = datetime(2026, 10, 28, 7, 30)
TUESDAY_BEFORE_WINDOW = datetime(2026, 10, 27, 6, 0)
TUESDAY_AFTER_WINDOW = datetime(2026, 10, 27, 9, 0)


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload or {}
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def make_service(
    forecast="2026-10-27T08:00:00+00:00",
    cancelled=False,
    display_as=None,
    reasons=None,
):
    temporal = {
        "departure": {
            "scheduleAdvertised": "2026-10-27T08:00:00+00:00",
            "realtimeForecast": forecast,
            "isCancelled": cancelled,
        }
    }
    if display_as:
        temporal["displayAs"] = display_as

    service = {
        "scheduleMetadata": {"uniqueIdentity": "G12345:2026-10-27"},
        "temporalData": temporal,
        "destination": [{"location": {"description": "London Paddington"}}],
        "locationMetadata": {"platform": {"planned": "3"}},
    }
    if reasons:
        service["reasons"] = reasons
    return service


class Network:
    """Records and answers the HTTP calls made by check_trains."""

    def __init__(self, services):
        self.services = services
        self.calls = []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url.endswith("/api/get_access_token"):
            return FakeResponse({"token": "access-token"})
        if url.endswith("/rtt/location"):
            return FakeResponse({"services": self.services})
        return FakeResponse()  # ntfy

    @property
    def notifications(self):
        topic_url = "https://ntfy.invalid/test-topic"
        return [c for c in self.calls if c[1] == topic_url]

    @property
    def departure_queries(self):
        return [c for c in self.calls if c[1].endswith("/rtt/location")]


@pytest.fixture
def run(trains, monkeypatch):
    """Run main() at a frozen time against a fake network."""

    def _run(services, now=TUESDAY_IN_WINDOW):
        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is not None:
                    return now.replace(tzinfo=timezone.utc).astimezone(tz)
                return now

        network = Network(services)
        monkeypatch.setattr(trains, "datetime", FrozenDatetime)
        monkeypatch.setattr(trains.requests, "request", network)
        monkeypatch.setattr(trains.time, "sleep", lambda _: None)
        trains.main()
        return network

    return _run


# ---------- Happy paths ----------

def test_on_time_train_sends_no_notification(run, capsys):
    network = run([make_service()])

    assert network.notifications == []
    assert "running normally" in capsys.readouterr().out


def test_cancelled_train_sends_high_priority_alert(run):
    network = run([make_service(cancelled=True)])

    assert len(network.notifications) == 1
    _, _, kwargs = network.notifications[0]
    assert kwargs["headers"]["Title"] == "Morning commute: CANCELLED"
    assert kwargs["headers"]["Priority"] == "high"
    assert kwargs["data"].decode() == (
        "08:00 to London Paddington, platform 3 is CANCELLED."
    )


def test_display_as_cancelled_is_treated_as_cancelled(run):
    network = run([make_service(display_as="CANCELLED")])

    assert len(network.notifications) == 1
    assert "CANCELLED" in network.notifications[0][2]["headers"]["Title"]


def test_minor_delay_sends_normal_priority_alert(run):
    network = run([make_service(forecast="2026-10-27T08:06:00+00:00")])

    assert len(network.notifications) == 1
    headers = network.notifications[0][2]["headers"]
    assert headers["Title"] == "Morning commute: DELAYED by 6 minutes"
    assert headers["Priority"] == "default"


def test_major_delay_sends_high_priority_alert(run):
    network = run([make_service(forecast="2026-10-27T08:12:00+00:00")])

    assert len(network.notifications) == 1
    headers = network.notifications[0][2]["headers"]
    assert headers["Title"] == "Morning commute: DELAYED by 12 minutes"
    assert headers["Priority"] == "high"


def test_delay_below_threshold_sends_no_notification(run):
    network = run([make_service(forecast="2026-10-27T08:04:00+00:00")])

    assert network.notifications == []


def test_alert_includes_first_reason(run):
    network = run([
        make_service(
            cancelled=True,
            reasons=[{"shortText": "a fault with the signalling"}],
        )
    ])

    message = network.notifications[0][2]["data"].decode()
    assert message.endswith("Reason: a fault with the signalling")


def test_only_the_configured_departure_is_matched(run):
    other = make_service(cancelled=True)
    other["temporalData"]["departure"]["scheduleAdvertised"] = (
        "2026-10-27T08:15:00+00:00"
    )

    network = run([other, make_service()])

    assert network.notifications == []


def test_departure_query_uses_configured_stations(run):
    network = run([make_service()])

    assert len(network.departure_queries) == 1
    params = network.departure_queries[0][2]["params"]
    assert params["code"] == "gb-nr:ABC"
    assert params["filterTo"] == "gb-nr:XYZ"
    assert params["timeFrom"] == "2026-10-27T06:30:00"
    assert params["timeTo"] == "2026-10-27T08:30:00"


def test_train_not_found_sends_no_notification(run, capsys):
    network = run([])

    assert network.notifications == []
    assert "Could not find 08:00 from ABC to XYZ" in capsys.readouterr().out


# ---------- README: duplicate suppression and state ----------

def test_same_alert_is_not_sent_twice_in_a_day(run, capsys):
    first = run([make_service(cancelled=True)])
    second = run([make_service(cancelled=True)])

    assert len(first.notifications) == 1
    assert second.notifications == []
    assert "Alert already sent" in capsys.readouterr().out


def test_state_is_persisted_for_the_service_and_day(run, trains):
    run([make_service(cancelled=True)])

    state = json.loads(trains.STATE_FILE.read_text())
    assert state == {"G12345:2026-10-27:CANCELLED": "2026-10-27"}


def test_worsening_to_cancelled_still_alerts_after_a_delay_alert(run):
    delayed = run([make_service(forecast="2026-10-27T08:06:00+00:00")])
    cancelled = run([make_service(cancelled=True)])

    assert len(delayed.notifications) == 1
    assert len(cancelled.notifications) == 1


def test_corrupt_state_file_is_reset(run, trains):
    trains.STATE_FILE.write_text("{not json")

    network = run([make_service(cancelled=True)])

    assert len(network.notifications) == 1


# ---------- README: commute days and checking windows ----------

def test_non_commute_day_exits_without_network_calls(run, capsys):
    network = run([make_service(cancelled=True)], now=WEDNESDAY_IN_WINDOW)

    assert network.calls == []
    assert "Not a configured commute day." in capsys.readouterr().out


@pytest.mark.parametrize(
    "now", [TUESDAY_BEFORE_WINDOW, TUESDAY_AFTER_WINDOW]
)
def test_outside_checking_window_exits_without_network_calls(
    run, capsys, now
):
    network = run([make_service(cancelled=True)], now=now)

    assert network.calls == []
    assert "Outside configured commute checking windows." in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize("hour,minute", [(7, 15), (8, 45)])
def test_window_boundaries_are_inclusive(run, hour, minute):
    network = run(
        [make_service()], now=datetime(2026, 10, 27, hour, minute)
    )

    assert len(network.departure_queries) == 1
