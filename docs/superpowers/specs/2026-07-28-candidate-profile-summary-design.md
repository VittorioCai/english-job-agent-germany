# Candidate profile summary update

## Goal

Improve the relevance of the jobs ranked by the English Job Agent for Germany by
giving the LLM a more accurate candidate profile. The update must not change the
pipeline, filters, thresholds, source coverage, or notification behavior.

## Scope

Change only the `cv_summary` value in `profile.yaml`.

Keep every other setting and file unchanged, including:

- `role_keywords`
- `field_keywords`
- `cities` and `germany_only`
- `german_level` and `apply_anyway`
- `min_score`
- source adapters, rule filters, LLM validation, ranking code, notifications,
  application tracking, and GitHub Actions

## Candidate positioning

The revised summary will tell the existing LLM judge to use this priority order:

1. Internships in Data Analysis, Business Intelligence, Business Analytics,
   Reporting, or Controlling
2. High-fit working student roles in the same fields
3. Internships or high-fit working student roles in Supply Chain, Procurement,
   Logistics, Operations Analytics, or Process Optimization
4. Product Analyst or Product Operations roles only when the work is substantially
   analytical

## Evidence included

The summary will use only experience already supported by the CV feedback:

- M.Sc. Management & Digital Technology at TUM
- Python, SQL/PostgreSQL, Excel/VBA, data visualization, and working knowledge of
  Power BI and Tableau
- Excel dashboards covering more than 50 enterprises and two recurring cost
  inefficiencies identified
- payroll automation saving more than 10 hours per month
- supplier and market-price tracking for procurement decisions
- a Python pipeline for approximately 59,000 firm-day news observations
- Fama-French regression analysis
- a PostgreSQL/pgvector patent-risk screening tool for non-technical users

## Location and language preferences

The summary will prefer the greater Stuttgart, Heilbronn, and Munich areas,
including surrounding towns, while remaining open to strong matches anywhere in
Germany.

German is A1. A higher German requirement must be treated as a risk and moderate
score penalty, not an automatic reason to discard an otherwise strong professional
match. The existing `apply_anyway: true` setting and current judging rules remain
unchanged.

## Verification

Verification will confirm that:

1. `profile.yaml` remains valid YAML.
2. Only the `cv_summary` value changed.
3. The existing automated test suite still passes.
4. The final Git diff contains no code or unrelated configuration changes.
