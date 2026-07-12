from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReadmeTests(unittest.TestCase):
    def test_readmes_document_penalty_without_score_cap(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("10-20", english)
        self.assertIn("10–20", chinese)
        self.assertNotIn("score is capped at 30", english)
        self.assertNotIn("限制在 30", chinese)

    def test_workflow_serializes_scans(self):
        workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", workflow)
        self.assertIn("cancel-in-progress: false", workflow)

    def test_community_documents_and_current_defaults_are_documented(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue((ROOT / "CONTRIBUTING.md").exists())
        self.assertTrue((ROOT / "SECURITY.md").exists())
        self.assertIn("Top 10", english)
        self.assertNotIn("add two secrets", english)


if __name__ == "__main__":
    unittest.main()
