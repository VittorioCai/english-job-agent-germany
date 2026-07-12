import os
import unittest
from unittest.mock import patch

from src import main
from src.sources.base import Job


JOB = Job("source:1", "Data Intern", "Example", "Berlin", "https://example.com/job", "data", "test", country="DE")
JUDGMENT = {
    "working_language": "English", "german_required": "none", "evidence": "English",
    "match_score": 80, "red_flags": [], "summary": "Good fit",
}


class Source:
    def __init__(self, *args, **kwargs):
        pass

    def fetch(self):
        return [JOB]


class MainTests(unittest.TestCase):
    def test_successful_judgment_is_saved_before_notification_failure(self):
        events = []

        def save_seen(seen):
            events.append(("save", set(seen)))

        def fail_notification(*args):
            events.append(("notify", None))
            raise RuntimeError("SMTP unavailable")

        profile = {"min_score": 30}
        companies = {"companies": []}
        with patch.object(main, "load_yaml", side_effect=[profile, companies]), \
             patch.object(main, "load_seen", return_value=set()), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ArbeitnowSource", Source), \
             patch.object(main, "ATSSource", Source), \
             patch("src.sources.workday.WorkdaySource", Source), \
             patch.object(main, "gate", return_value=("pass", "ok")), \
             patch("src.filters.llm_judge.judge", return_value=JUDGMENT), \
             patch.object(main, "save_seen", side_effect=save_seen), \
             patch("src.notify.email.send_digest", side_effect=fail_notification), \
             patch.dict(os.environ, {"NOTIFY": "email"}):
            with self.assertRaisesRegex(RuntimeError, "SMTP unavailable"):
                main.run()

        self.assertEqual(events[0], ("save", {JOB.id}))
        self.assertEqual(events[1][0], "notify")


if __name__ == "__main__":
    unittest.main()
