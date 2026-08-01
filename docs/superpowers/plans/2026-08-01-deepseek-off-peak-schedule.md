# DeepSeek Off-Peak Schedule Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Queue the daily workflow at 10:20 Europe/Berlin and prevent official DeepSeek runs from starting during the announced Beijing peak-price windows.

**Architecture:** Add one standard-library Python guard that computes a delay from an injected current time and sleeper, then call it in GitHub Actions immediately before the pipeline. Keep GitHub's timezone-aware schedule, and document that both enqueue and delivery are best-effort rather than exact.

**Tech Stack:** Python 3.12 standard library (`datetime`, `zoneinfo`, `unittest`), GitHub Actions YAML, Markdown.

---

### Task 1: Add the DeepSeek peak-window guard

**Files:**
- Create: `scripts/wait_for_deepseek_off_peak.py`
- Create: `tests/test_off_peak.py`

**Step 1: Write the failing tests**

Create `tests/test_off_peak.py`:

```python
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
```

**Step 2: Run the new test to verify it fails**

Run: `python -m unittest tests.test_off_peak -v`

Expected: ERROR with `ModuleNotFoundError` because the guard module does not exist yet.

**Step 3: Write the minimal implementation**

Create `scripts/wait_for_deepseek_off_peak.py`:

```python
"""Delay official DeepSeek runs until Beijing off-peak pricing begins."""

import math
import os
import time
from datetime import datetime, time as clock_time, timedelta
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")
BUFFER = timedelta(minutes=5)
PEAK_WINDOWS = (
    (clock_time(9), clock_time(12)),
    (clock_time(14), clock_time(18)),
)


def wait_seconds(now: datetime) -> int:
    local = now.astimezone(BEIJING)
    current = local.time().replace(tzinfo=None)
    for start, end in PEAK_WINDOWS:
        if start <= current < end:
            allowed = datetime.combine(local.date(), end, tzinfo=BEIJING) + BUFFER
            return max(0, math.ceil((allowed - local).total_seconds()))
    return 0


def wait_for_off_peak(provider: str, now: datetime, sleeper=time.sleep) -> int:
    if provider.strip().lower() != "deepseek":
        print(f"[pricing] provider {provider or 'unset'}; no DeepSeek wait")
        return 0

    seconds = wait_seconds(now)
    if seconds:
        allowed = now.astimezone(BEIJING) + timedelta(seconds=seconds)
        print(
            f"[pricing] DeepSeek peak window; waiting {seconds}s until "
            f"{allowed:%Y-%m-%d %H:%M:%S %Z}",
            flush=True,
        )
        sleeper(seconds)
    else:
        print("[pricing] DeepSeek off-peak window; starting now")
    return seconds


def main() -> None:
    provider = os.environ.get("LLM_PROVIDER") or "anthropic"
    wait_for_off_peak(provider, datetime.now(BEIJING))


if __name__ == "__main__":
    main()
```

**Step 4: Run the new test to verify it passes**

Run: `python -m unittest tests.test_off_peak -v`

Expected: 4 tests pass.

**Step 5: Run the full unit suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

**Step 6: Commit**

```bash
git add scripts/wait_for_deepseek_off_peak.py tests/test_off_peak.py
git commit -m "feat: guard DeepSeek peak pricing"
```

### Task 2: Change the enqueue time and document runtime behavior

**Files:**
- Modify: `.github/workflows/daily.yml`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `tests/test_readme.py`

**Step 1: Update the schedule/documentation test first**

Replace `test_schedule_runs_after_morning_posting_window_in_berlin_time` in
`tests/test_readme.py` with:

```python
    def test_schedule_and_deepseek_peak_guard_are_documented(self):
        workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

        self.assertIn('cron: "20 10 * * *"', workflow)
        self.assertIn('timezone: "Europe/Berlin"', workflow)
        self.assertIn("Wait for DeepSeek off-peak pricing", workflow)
        self.assertIn("scripts/wait_for_deepseek_off_peak.py", workflow)
        self.assertIn("10:20 Europe/Berlin", english)
        self.assertIn("10:20 Europe/Berlin", chinese)
        self.assertIn("09:00–12:00", english)
        self.assertIn("09:00–12:00", chinese)
        self.assertIn("no exact delivery time is guaranteed", english)
        self.assertIn("不保证准确的执行或邮件送达时间", chinese)
```

**Step 2: Run the targeted test to verify it fails**

Run: `python -m unittest tests.test_readme.ReadmeTests.test_schedule_and_deepseek_peak_guard_are_documented -v`

Expected: FAIL because the workflow still queues at 11:20 and has no guard step.

**Step 3: Change the workflow schedule and add the guard step**

In `.github/workflows/daily.yml`, change the scheduled trigger to:

```yaml
  schedule:
    - cron: "20 10 * * *"
      timezone: "Europe/Berlin"
```

Immediately after the existing test step and before `Run pipeline`, add:

```yaml
      - name: Wait for DeepSeek off-peak pricing
        env:
          LLM_PROVIDER: ${{ vars.LLM_PROVIDER || 'anthropic' }}
        run: python scripts/wait_for_deepseek_off_peak.py
```

**Step 4: Update both README schedule sections**

Replace the English timing paragraph with:

```markdown
GitHub queues the scan daily at 10:20 Europe/Berlin. Scheduled workflows are
best-effort, so execution and digest delivery may be delayed; no exact delivery time
is guaranteed. With `LLM_PROVIDER=deepseek`, the workflow treats 09:00–12:00 and
14:00–18:00 Asia/Shanghai as peak-pricing windows. A run that starts in either
window waits until 12:05 or 18:05 Beijing time before starting the pipeline; a run
already in an off-peak window starts immediately.
```

Replace the Chinese timing paragraph with:

```markdown
GitHub 每天在 10:20 Europe/Berlin 将扫描加入队列。定时工作流可能延迟,
因此不保证准确的执行或邮件送达时间。当 `LLM_PROVIDER=deepseek` 时,工作流
将北京时间 09:00–12:00 和 14:00–18:00 视为峰价时段。如果运行在峰段开始,
会等到北京时间 12:05 或 18:05 再启动流水线;已经处于谷段则立即运行。
```

**Step 5: Run targeted and full tests**

Run: `python -m unittest tests.test_readme -v`

Expected: all README tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

**Step 6: Commit**

```bash
git add .github/workflows/daily.yml README.md README.zh-CN.md tests/test_readme.py
git commit -m "chore: schedule DeepSeek usage off peak"
```

### Task 3: Verify and publish directly to main

**Files:**
- Verify only; no expected file changes.

**Step 1: Run complete verification**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `python -m compileall -q job_agent scripts tests`

Expected: exit code 0.

Run: `LLM_PROVIDER=anthropic python scripts/wait_for_deepseek_off_peak.py`

Expected: exits immediately and prints that no DeepSeek wait is required.

Run: `git diff --check origin/main...HEAD`

Expected: no output.

**Step 2: Inspect the final diff and remote position**

Run: `git fetch origin main && git status --short --branch && git diff --stat origin/main...HEAD && git log --oneline origin/main..HEAD`

Expected: clean `main`, ahead only by the design, plan, guard, tests, workflow,
and README commits created for this change.

**Step 3: Push directly to main**

Run: `git push origin main`

Expected: `main` advances successfully without creating a pull request.

**Step 4: Verify the published head**

Run: `git fetch origin main && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" && git status --short --branch`

Expected: local `main` and `origin/main` match and the worktree is clean.

Do not manually dispatch the production workflow. The next scheduled run is the
end-to-end validation because a peak-time manual run could intentionally occupy a
runner until the price window ends.
