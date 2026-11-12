# UK Train Alerts

<TBC>

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
