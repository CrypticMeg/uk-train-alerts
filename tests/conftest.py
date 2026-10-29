"""Shared pytest setup.

check_trains reads env vars and config.yaml at import time, so we prepare a
hermetic environment before the module is first imported.
"""
import importlib
import os
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config.yaml"
EXAMPLE_CONFIG_FILE = PROJECT_DIR / "config.example.yaml"

# Make `import check_trains` work regardless of how pytest is invoked.
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Always use dummy values so tests can never hit a real ntfy topic or RTT
# account. load_dotenv() does not override variables that are already set.
os.environ["RTT_API_TOKEN"] = "test-rtt-token"
os.environ["NTFY_TOPIC_URL"] = "https://ntfy.invalid/test-topic"


def _import_check_trains():
    """Import check_trains using config.example.yaml instead of config.yaml."""
    original_open = Path.open

    def open_redirected(self, *args, **kwargs):
        if self == CONFIG_FILE:
            self = EXAMPLE_CONFIG_FILE
        return original_open(self, *args, **kwargs)

    Path.open = open_redirected
    try:
        return importlib.import_module("check_trains")
    finally:
        Path.open = original_open


check_trains = _import_check_trains()


@pytest.fixture(scope="session")
def trains():
    """Return the imported check_trains module."""
    return check_trains


@pytest.fixture(autouse=True)
def isolated_state_file(tmp_path, monkeypatch):
    """Keep tests from reading or writing the real state.json."""
    monkeypatch.setattr(check_trains, "STATE_FILE", tmp_path / "state.json")
