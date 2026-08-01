import unittest
from unittest.mock import Mock, patch

from src.sources.arbeitnow import ArbeitnowSource


class ArbeitnowTests(unittest.TestCase):
    @patch("src.sources.arbeitnow.requests.get")
    def test_normalizes_object_tags_and_discards_unsupported_values(self, get):
        get.return_value = Mock()
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {
            "data": [
                {
                    "slug": "data-intern",
                    "title": "Data Intern",
                    "company_name": "Acme",
                    "location": "Berlin",
                    "url": "https://example.com/data-intern",
                    "description": "<p>Analyze data</p>",
                    "remote": False,
                    "tags": {"0": "Remote", "1": None, "2": "Data"},
                    "job_types": ["Intern", 7],
                },
                {
                    "slug": "finance-intern",
                    "title": "Finance Intern",
                    "company_name": "Acme",
                    "location": "Munich",
                    "url": "https://example.com/finance-intern",
                    "description": "Finance",
                    "remote": False,
                    "tags": "Finance",
                    "job_types": None,
                },
            ],
            "links": {"next": None},
        }

        jobs = ArbeitnowSource(max_pages=1).fetch()

        self.assertEqual(jobs[0].tags, ["Remote", "Data", "Intern"])
        self.assertEqual(jobs[1].tags, [])


if __name__ == "__main__":
    unittest.main()
