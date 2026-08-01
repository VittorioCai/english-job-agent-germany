import unittest
from datetime import datetime
from unittest.mock import Mock

from scripts.wait_for_deepseek_off_peak import (
    BEIJING,
    wait_for_off_peak,
    wait_seconds,
)


class OffPeakTests(unittest.TestCase):
    def test_peak_windows_wait_until_five_minutes_after_end(self):
        cases = {
            (9, 0): 3 * 60 * 60 + 5 * 60,
            (11, 30): 35 * 60,
            (14, 0): 4 * 60 * 60 + 5 * 60,
            (17, 59): 6 * 60,
        }

        for (hour, minute), expected in cases.items():
            with self.subTest(hour=hour, minute=minute):
                now = datetime(2026, 8, 1, hour, minute, tzinfo=BEIJING)
                self.assertEqual(wait_seconds(now), expected)

    def test_end_boundaries_and_midday_are_off_peak(self):
        for hour, minute in ((12, 0), (13, 30), (18, 0)):
            with self.subTest(hour=hour, minute=minute):
                now = datetime(2026, 8, 1, hour, minute, tzinfo=BEIJING)
                self.assertEqual(wait_seconds(now), 0)

    def test_non_deepseek_provider_never_sleeps(self):
        sleeper = Mock()
        now = datetime(2026, 8, 1, 16, 20, tzinfo=BEIJING)

        self.assertEqual(wait_for_off_peak("anthropic", now, sleeper), 0)
        sleeper.assert_not_called()

    def test_deepseek_provider_sleeps_for_peak_delay(self):
        sleeper = Mock()
        now = datetime(2026, 8, 1, 16, 20, tzinfo=BEIJING)

        self.assertEqual(wait_for_off_peak("deepseek", now, sleeper), 105 * 60)
        sleeper.assert_called_once_with(105 * 60)


if __name__ == "__main__":
    unittest.main()
