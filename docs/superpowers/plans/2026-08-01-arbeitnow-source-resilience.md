# Arbeitnow Source Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept Arbeitnow's observed object-shaped tag metadata and keep the daily pipeline running when any one source adapter raises unexpectedly.

**Architecture:** Normalize Arbeitnow's JSON-only array/object metadata at the adapter boundary so every `Job` keeps a list of strings. Add a second exception boundary around each top-level source fetch so one adapter failure is logged and omitted while later sources continue through the unchanged pipeline.

**Tech Stack:** Python 3.12, `unittest`, `unittest.mock`, GitHub Actions

---

### Task 1: Normalize Arbeitnow tag metadata

**Files:**
- Create: `tests/test_arbeitnow.py`
- Modify: `src/sources/arbeitnow.py:15-50`

- [ ] **Step 1: Write the failing adapter regression test**

```python
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
```

- [ ] **Step 2: Run the adapter test and verify the regression is red**

Run: `python -m unittest tests.test_arbeitnow -v`

Expected: FAIL with `TypeError: unsupported operand type(s) for +: 'dict' and 'list'`.

- [ ] **Step 3: Add the minimal array/object string normalizer**

Insert above `ArbeitnowSource` in `src/sources/arbeitnow.py`:

```python
def _string_list(value) -> list[str]:
    if isinstance(value, dict):
        values = value.values()
    elif isinstance(value, list):
        values = value
    else:
        return []
    return [item for item in values if isinstance(item, str)]
```

Replace the `tags` constructor argument with:

```python
tags=_string_list(j.get("tags")) + _string_list(j.get("job_types")),
```

- [ ] **Step 4: Run the adapter test and the full suite**

Run: `python -m unittest tests.test_arbeitnow -v`

Expected: one test passes.

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the adapter fix**

```bash
git add src/sources/arbeitnow.py tests/test_arbeitnow.py
git commit -m "fix: normalize Arbeitnow tag metadata"
```

### Task 2: Isolate top-level source failures

**Files:**
- Modify: `tests/test_main.py`
- Modify: `src/main.py:171-178`

- [ ] **Step 1: Write the failing pipeline resilience test**

Add to `MainTests` in `tests/test_main.py`:

```python
    def test_source_failure_does_not_stop_later_sources(self):
        class BrokenSource(Source):
            name = "broken"

            def fetch(self):
                raise RuntimeError("schema changed")

        output = StringIO()
        with patch.object(main, "load_yaml",
                          side_effect=[{"min_score": 30}, {"companies": []}]), \
             patch.object(main, "load_seen", return_value={}), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ATSSource", BrokenSource), \
             patch.object(main, "ArbeitnowSource", Source), \
             patch("src.sources.workday.WorkdaySource", EmptySource), \
             patch.object(main, "gate", return_value=("pass", "ok")), \
             redirect_stdout(output):
            try:
                main.run(dry_run=True)
            except RuntimeError as error:
                self.fail(f"pipeline stopped after one source failed: {error}")

        self.assertIn("[source] broken failed: schema changed", output.getvalue())
        self.assertIn("PASS  Data Intern @ Example (Berlin)", output.getvalue())
```

- [ ] **Step 2: Run the pipeline test and verify it is red**

Run: `python -m unittest tests.test_main.MainTests.test_source_failure_does_not_stop_later_sources -v`

Expected: FAIL with `pipeline stopped after one source failed: schema changed`.

- [ ] **Step 3: Add the top-level source exception boundary**

Replace the source loop in `src/main.py` with:

```python
    sources = (
        ATSSource(companies),
        PersonioSource(companies),
        SmartRecruitersSource(companies),
        RecruiteeSource(companies),
        WorkdaySource(companies, skip_ids=seen),
        ArbeitnowSource(),
    )
    jobs = []
    for source in sources:
        try:
            jobs.extend(source.fetch())
        except Exception as error:
            source_name = getattr(source, "name", source.__class__.__name__)
            print(f"[source] {source_name} failed: {error}")
```

- [ ] **Step 4: Run the targeted test and the full suite**

Run: `python -m unittest tests.test_main.MainTests.test_source_failure_does_not_stop_later_sources -v`

Expected: one test passes.

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the pipeline isolation**

```bash
git add src/main.py tests/test_main.py
git commit -m "fix: isolate job source failures"
```

### Task 3: Verify and publish to main

**Files:**
- Verify: `src/sources/arbeitnow.py`
- Verify: `src/main.py`
- Verify: `tests/test_arbeitnow.py`
- Verify: `tests/test_main.py`

- [ ] **Step 1: Run static and unit verification**

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```

Expected: all tests pass, compilation exits zero, and `git diff --check` prints nothing.

- [ ] **Step 2: Run the live public-feed dry run**

Run: `python -m src.main --dry-run`

Expected: the command exits zero, Arbeitnow reports a job count, cross-source deduplication and rule-gate summaries print, and no LLM or notification operation runs.

- [ ] **Step 3: Confirm scope and remote position**

```bash
git status -sb
git log --oneline origin/main..HEAD
git fetch origin
git rev-list --left-right --count origin/main...HEAD
```

Expected: only the approved commits are ahead of `origin/main`, and the branch is not behind.

- [ ] **Step 4: Push the verified commits directly to main**

Run: `git push origin main`

Expected: GitHub accepts the fast-forward update to `main`.

- [ ] **Step 5: Dispatch and watch the production workflow**

```bash
gh workflow run daily.yml --repo VittorioCai/english-job-agent-germany --ref main
gh run list --repo VittorioCai/english-job-agent-germany --workflow daily.yml --event workflow_dispatch --limit 1
```

Watch the returned run until completion with `gh run watch <run-id> --repo VittorioCai/english-job-agent-germany --exit-status`.

Expected: `Run tests`, `Run pipeline`, and `Persist scan state` finish successfully. Record the run URL and report any residual external-source warnings without treating an isolated source warning as a workflow failure.
