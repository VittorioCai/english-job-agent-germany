# Candidate Profile Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace only the candidate `cv_summary` so the existing LLM judge ranks internships and high-fit working student roles against the candidate's actual experience and preferences.

**Architecture:** Keep the complete job collection, filtering, scoring, and notification pipeline unchanged. Update the trusted candidate context already passed to the LLM through `profile.yaml`, then compare the parsed configuration against the committed version to prove that no other setting changed.

**Tech Stack:** YAML, Python 3.12, PyYAML, unittest

---

### Task 1: Update and verify the candidate profile summary

**Files:**
- Modify: `profile.yaml`
- Test: existing test suite under `tests/`

- [ ] **Step 1: Replace only `cv_summary` in `profile.yaml`**

Use this exact YAML value:

```yaml
cv_summary: |
  M.Sc. Management & Digital Technology student at TUM seeking internships
  as the first priority, while remaining open to high-fit working student roles.

  Primary targets: Data Analyst, Business Intelligence, Business Analytics,
  Reporting, and Controlling. Secondary targets: Supply Chain, Procurement,
  Logistics, Operations Analytics, and Process Optimization. Also open to
  Product Analyst or Product Operations roles with substantial analytical work.

  Skills include Python, SQL/PostgreSQL, Excel/VBA, data visualization, and
  working knowledge of Power BI and Tableau. Built Excel dashboards covering
  50+ enterprises, identified two recurring cost inefficiencies, and automated
  payroll calculations that saved more than 10 hours per month. Also developed
  a supplier and market-price tracking database to support procurement decisions.

  Co-developed a Python data pipeline for approximately 59,000 firm-day news
  observations and evaluated portfolio performance using Fama-French regressions.
  Designed a PostgreSQL/pgvector database and user interface for an AI patent-risk
  screening tool used by non-technical users.

  Prefer internships over working student positions. Prefer the greater Stuttgart,
  Heilbronn, and Munich areas, including surrounding towns, but consider strong
  matches anywhere in Germany. German is currently A1. Do not reject an otherwise
  strong role solely because it lists a higher German requirement; flag the
  language risk and reduce the score moderately.
```

- [ ] **Step 2: Verify the YAML parses and contains the intended evidence**

Run:

```bash
python - <<'PY'
from pathlib import Path
import yaml

profile = yaml.safe_load(Path("profile.yaml").read_text(encoding="utf-8"))
summary = profile["cv_summary"]

required = [
    "internships",
    "high-fit working student roles",
    "Data Analyst",
    "Supply Chain",
    "Product Analyst",
    "50+ enterprises",
    "10 hours per month",
    "59,000 firm-day",
    "PostgreSQL/pgvector",
    "surrounding towns",
    "strong matches anywhere in Germany",
    "German is currently A1",
]
missing = [item for item in required if item not in summary]
assert not missing, f"missing profile evidence: {missing}"
print("profile summary validation: PASS")
PY
```

Expected: `profile summary validation: PASS`

- [ ] **Step 3: Prove every non-summary configuration value is unchanged**

Run:

```bash
python - <<'PY'
import subprocess
from pathlib import Path
import yaml

before = yaml.safe_load(subprocess.check_output(
    ["git", "show", "HEAD:profile.yaml"], text=True
))
after = yaml.safe_load(Path("profile.yaml").read_text(encoding="utf-8"))

before.pop("cv_summary")
after.pop("cv_summary")
assert before == after, "a profile setting other than cv_summary changed"
print("non-summary configuration comparison: PASS")
PY
```

Expected: `non-summary configuration comparison: PASS`

- [ ] **Step 4: Run formatting and regression checks**

Run:

```bash
git diff --check
python -m unittest discover -s tests -v
```

Expected: no diff errors and all existing tests pass.

- [ ] **Step 5: Review the final diff**

Run:

```bash
git diff -- profile.yaml
git status --short
```

Expected: `profile.yaml` is the only implementation file modified. The diff changes only the `cv_summary` block.

- [ ] **Step 6: Commit the configuration update**

```bash
git add profile.yaml
git commit -m "config: sharpen candidate job profile"
```
