# Developing

How to work on this repository. For what the system does, see the
[design](design.md).

The project is developed behaviour-first. Expected behaviour is written as
Gherkin scenarios in `features/` and run with
[pytest-bdd](https://pytest-bdd.readthedocs.io/). Unit tests then drive out
the implementation underneath them.

## Set up

Dependencies are declared in `pyproject.toml`. Python 3.13 is required.

On Debian, install them with APT:

```bash
sudo apt install python3-requests python3-yaml python3-dotenv \
    python3-pytest python3-pytest-bdd pycodestyle pydocstyle
```

Or, in a virtual environment:

```bash
pip install -e '.[dev]'
```

pytest-bdd is held below version 8 to match the version Debian packages, so
both environments read the feature files the same way. Version 7 does not
support the Gherkin `Rule:` keyword, so rules are written as `# Rule:`
comments for now.

## Check your work

```bash
make check            # lint and test: run this before merging
make lint             # pycodestyle and pydocstyle
make test             # every test suite
make test-smoke       # smoke tests for the proof-of-concept script
make test-unit        # unit tests for the train_alerts package
make test-acceptance  # Gherkin scenarios against the train_alerts package
```

All acceptance tests are currently skipped, because their steps and the
package are not written yet. Run `pytest -rs tests/acceptance` to see why each
one is skipped.

## Layout

```text
features/          Gherkin scenarios: the specification
diagrams/          design diagrams
documents/         documentation
train_alerts/      the package
check_trains.py    the proof of concept
tests/conftest.py  dummy credentials, so no test can reach RTT or ntfy
tests/smoke/       proof-of-concept tests, removed along with check_trains.py
tests/unit/        unit tests, one component at a time
tests/acceptance/  scenario bindings, step definitions and fakes
```

## Code style

- Lines are at most 79 characters, checked by `pycodestyle`.
- Every module, class and function has a docstring, checked by `pydocstyle`.
  The first line is a short imperative sentence.
- `make lint` must be clean before merging, as part of `make check`.

## Tests

Development is both behaviour-driven (BDD) and test-driven (TDD). The
scenarios in `features/` say what the system does. Unit tests drive out how.

- `tests/conftest.py` sets dummy credentials, so no test can reach the real
  RTT API or ntfy topic.
- Every scenario in `features/` is bound to a test in `tests/acceptance/`,
  and stays skipped until its feature is built. Scenarios tagged `@assumption`
  describe behaviour that has not been confirmed, and have their own skip
  reason.
- Unit tests are in `tests/unit/`, and test one component at a time.
- Tests use fakes at the edges: train data, notifier, calendar, state and
  clock. They never use the network.

### The cycle within a feature

1. Write a unit test and watch it fail.
2. Write the code to make it pass.
3. Repeat until the units cover the feature.
4. Unskip the feature's acceptance tests and make them pass.

A feature is finished when its acceptance tests are unskipped and green.

## Branching

- `main` holds reviewed, working code, and is what gets released.
- `development` is where finished features are merged.
- `feature/<name>` branches hold work in progress.
- `debian/latest` holds the packaging. See below.

A feature branch is merged to `development` only when it is green and
unskipped, and `make check` is clean. `development` is merged to `main` when the change has been reviewed and the features for the release
are in place.

## Debian packaging

The service is deployed as the Debian package `python3-uk-train-alerts`, so
every runtime dependency must be available as a Debian package. This is why
the development dependencies above are installed with APT.

Packaging lives on its own branch, `debian/latest`, which holds the `debian/`
directory. It is kept up to date by merging `main` into it, and `debian/` is
never on `main`.

Versions are `major.minor.patch`. To make a release:

1. Tag a working version on `main`, for example `0.1.0`.
2. Check out `debian/latest` and merge `main` into it.
3. Build the package and release it.
4. Tag the packaging commit with the upstream version plus the Debian
   revision, for example `0.1.0-1`.

A `release` target in the Makefile will run the build and release steps. It
doesn't exist yet, and neither does `debian/latest`.
