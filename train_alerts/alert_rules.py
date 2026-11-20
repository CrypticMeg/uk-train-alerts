"""Apply train notification rules."""
from typing import Optional


class AlertRules:
    """Apply domain rules to train status changes."""

    def __init__(self, delay_band_size: int) -> None:
        """Store the configured delay band size."""
        self._delay_band_size = delay_band_size

    def delay_band(self, delay_minutes: int) -> int:
        """Return the delay band, treating early trains as on time."""
        return max(0, delay_minutes // self._delay_band_size)

    def should_notify_delay(
        self,
        previous_band: Optional[int],
        current_delay_minutes: int,
    ) -> bool:
        """Return whether the delay moved to a different band."""
        if previous_band is None:
            previous_band = 0

        return self.delay_band(current_delay_minutes) != previous_band
