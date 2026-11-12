# Agent instructions

UK Train Alerts notifies a traveller when a planned train changes. Read the
[README](README.md) first, then the [design](documents/design.md). The
scenarios in `features/` are the authoritative specification. How to work in
this repository is in [developing](documents/developing.md); follow it.

Run `make check` (lint and every test suite) before saying work is done.

## Process

This project is built behaviour-first and test-first, and the process matters
as much as the code. Do not skip steps to reach working code faster.

- Write a failing unit test before the code that makes it pass.
- Leave a feature's acceptance tests skipped until its unit work is green,
  then unskip them.
- Do not edit `features/` without asking.
- Scenarios tagged `@assumption` are unconfirmed. Ask, rather than choosing an
  answer.
- Do not extend `check_trains.py`. It is a proof of concept that will be
  removed.
- Briefly explain why as you go, as the author is still learning the process.

## Boundaries

- Never read or change `.env` or `config.yaml`.
- Tests never use the network.
- Keep the change as small as it can be.
- Do not commit or push unless asked.
