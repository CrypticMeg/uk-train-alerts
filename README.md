# UK Train Alerts

This is an alert system for changes in planned train journeys. It alerts the user when their planned train journey is cancelled or delayed. It delivers updates on changes in status and gives the user sufficient information to allow them to consider alternative journey options (without the user having to actively seek out this information). It is useful for any commuter or train traveller with a planned journey.

## Running locally

You need Python 3.13, a Realtime Trains refresh token and an ntfy topic.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp config.example.yaml config.yaml
cp .env.example .env
```

Edit `config.yaml` with your journeys and `.env` with your token and topic,
then run:

```bash
python check_trains.py
```

This runs the proof-of-concept script, which is the only implementation so
far. See the [design](documents/design.md) for where it is heading.

## Documents

- [Design](documents/design.md): what the system does and why it is shaped
  that way.
- [Developing](documents/developing.md): working on the repository.
