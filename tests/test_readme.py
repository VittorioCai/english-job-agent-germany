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


if __name__ == "__main__":
    unittest.main()
