"""Test the alert rules."""
import pytest

from train_alerts.alert_rules import AlertRules


@pytest.fixture
def rules():
    """Create alert rules with a five-minute delay band."""
    return AlertRules(delay_band_size=5)


@pytest.mark.parametrize(
    ("delay_minutes", "expected_band"),
    [
        (-2, 0),
        (0, 0),
        (4, 0),
        (5, 1),
        (9, 1),
        (10, 2),
    ],
)
def test_delay_band_clamps_early_trains_to_zero(
    rules, delay_minutes, expected_band
):
    """Treat early trains as on time and floor other delays by band size."""
    assert rules.delay_band(delay_minutes) == expected_band


def test_first_check_notifies_when_train_is_already_delayed(rules):
    """Treat the previous delay band as zero on the first check."""
    assert rules.should_notify_delay(None, 7)
    assert not rules.should_notify_delay(None, 4)


@pytest.mark.parametrize(
    ("previous_band", "current_delay"),
    [
        (0, 5),
        (0, 6),
        (1, 10),
        (0, 12),
        (2, 8),
        (3, 9),
        (2, 9),
        (1, 2),
        (1, 4),
        (1, -1),
    ],
)
def test_notify_when_delay_band_changes(rules, previous_band, current_delay):
    """Notify when the current delay enters a different band."""
    assert rules.should_notify_delay(previous_band, current_delay)


@pytest.mark.parametrize(
    ("previous_band", "current_delay"),
    [
        (0, -2),
        (0, 4),
        (1, 9),
        (2, 10),
        (0, 3),
    ],
)
def test_do_not_notify_when_delay_stays_in_same_band(
    rules, previous_band, current_delay
):
    """Suppress notifications when the delay remains in the same band."""
    assert not rules.should_notify_delay(previous_band, current_delay)


def test_notify_on_every_crossing_of_a_delay_band(rules):
    """Notify each time successive checks cross a delay band boundary."""
    previous_band = 1

    for delay_minutes in (10, 9, 10):
        assert rules.should_notify_delay(previous_band, delay_minutes)
        previous_band = rules.delay_band(delay_minutes)
