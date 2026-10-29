# UK Train Alerts

A small Python service that monitors specified UK rail journeys using the
[Realtime Trains Next-Generation API](https://api-portal.rtt.io/) and sends
notifications through [ntfy](https://ntfy.sh/) when a selected train is
cancelled or delayed.

It is designed for a regular commute: rather than monitoring an entire
station, it watches particular scheduled departures during configured time
windows and alerts only when their status changes materially.

## Features

- Monitors one or more regular train journeys
- Matches trains by origin, destination, and scheduled departure time
- Sends alerts for cancellations and delays
- Supports separate normal and high-priority notifications
- Avoids duplicate alerts for the same service and day
- Configurable commute days and checking windows
- Designed to run on macOS with `launchd`, or on an always-on Linux server

## Requirements

- Python 3.9 or later
- A Realtime Trains API account and refresh token
- An ntfy topic and the ntfy mobile app, or another ntfy-compatible client

Realtime Trains provides UK rail running information, including live
departure forecasts and cancellation data. Check the terms of your RTT API
plan before deploying the service.

## Installation

Clone the repository:

```bash
git clone [https://github.com/CrypticMeg/uk-train-alerts.git](https://github.com/CrypticMeg/uk-train-alerts.git)
cd uk-train-alerts
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the example configuration files:

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

Edit `config.yaml` to define your journeys:

```yaml
commute_days:
  - Tuesday
  - Friday

state_file: state.json

alerts:
  delay_minutes: 5
  major_delay_minutes: 10

journeys:
  - label: "Morning commute"
    origin: "ABC"
    destination: "XYZ"
    scheduled_departure: "08:00"
    check_from: "07:15"
    check_to: "08:45"
```

- `commute_days` controls the days on which the script runs.
- `origin` and `destination` are station CRS or short codes.
- `scheduled_departure` is the advertised departure time of the train you
  normally catch.
- `check_from` and `check_to` define the period during which the script will
  check that journey.
- `delay_minutes` is the threshold for a normal-priority delay alert.
- `major_delay_minutes` is the threshold for a high-priority delay alert.

Edit `.env` with your own credentials:

```dotenv
RTT_API_TOKEN=your_realtime_trains_refresh_token
NTFY_TOPIC_URL=[https://ntfy.sh/your-private-random-topic](https://ntfy.sh/your-private-random-topic)
```

Do not commit `.env`, `config.yaml`, `state.json`, or logs.

## Running manually

```bash
source .venv/bin/activate
python check_trains.py
```

The script exits immediately if today is not a configured commute day or if
the current time is outside every journey’s checking window.

## Notifications

Install the ntfy app on your phone and subscribe to the same topic name used
in `NTFY_TOPIC_URL`.

Use a long, random topic name. On the public ntfy service, anyone who knows
the topic name can publish messages to it.

Example notification:

```text
Morning commute: CANCELLED
08:00 to London Paddington, platform 3 is CANCELLED.
```

## Scheduling on macOS

Create a `launchd` agent to run the script every three minutes:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>uk.example.trainalerts</string>

  <key>ProgramArguments</key>
  <array>
    <string>/path/to/uk-train-alerts/.venv/bin/python</string>
    <string>/path/to/uk-train-alerts/check_trains.py</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/path/to/uk-train-alerts</string>

  <key>StartInterval</key>
  <integer>180</integer>

  <key>RunAtLoad</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/path/to/uk-train-alerts/logs/stdout.log</string>

  <key>StandardErrorPath</key>
  <string>/path/to/uk-train-alerts/logs/stderr.log</string>
</dict>
</plist>
```

Save it as:

```bash
~/Library/LaunchAgents/uk.example.trainalerts.plist
```

Then load it:

```bash
mkdir -p /path/to/uk-train-alerts/logs
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/uk.example.trainalerts.plist
launchctl kickstart gui/$(id -u)/uk.example.trainalerts
```

The script itself checks whether today is a configured commute day and whether
the current time falls within a journey’s checking window.

## Important limitation: sleeping computers

A sleeping MacBook will not reliably run scheduled jobs during the sleep
period. For morning alerts, either leave the computer awake, schedule it to
wake before the checking window using `pmset`, or run the service on an
always-on computer or server.

Example:

```bash
sudo pmset repeat wake MTWRF 06:45:00
```

## Security

- Keep `.env` private; it contains your RTT refresh token and notification
  topic.
- Keep `config.yaml` private if it contains your real commute pattern.
- Use a long random ntfy topic name.
- Do not commit API tokens, JWTs, or notification URLs.
- If a credential is exposed, revoke or rotate it immediately.

## License

This project is licensed under the [MIT License](LICENSE).