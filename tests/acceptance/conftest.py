"""Shared pytest setup for the acceptance tests."""
import pytest


def pytest_collection_modifyitems(items):
    """Give unconfirmed assumptions their own skip reason."""
    for item in items:
        if item.get_closest_marker("assumption"):
            item.add_marker(
                pytest.mark.skip(reason="unconfirmed assumption")
            )
