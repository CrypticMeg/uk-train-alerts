"""Pytest setup for the PoC smoke tests.

check_trains reads env vars and config.yaml at import time, so we prepare a
hermetic environment before the module is first imported. The dummy env vars
come from tests/conftest.py, which pytest loads before this file.

Delete this directory along with the PoC.
"""
import importlib
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_DIR / "config.yaml"
EXAMPLE_CONFIG_FILE = PROJECT_DIR / "config.example.yaml"


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
