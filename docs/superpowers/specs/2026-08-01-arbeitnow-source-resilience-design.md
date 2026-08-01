# Arbeitnow Source Resilience Design

## Goal

Restore the daily scan after Arbeitnow returned a posting whose `tags` field was a
JSON object instead of the documented array shape. Future failures in one source
must not prevent usable jobs from the remaining sources from reaching the digest.

## Scope

The change is limited to source ingestion and its tests. It does not change job
ranking, German-language detection, LLM budgets, notification content, persisted
state formats, or the workflow schedule.

## Arbeitnow normalization

Add a small normalization helper in `src/sources/arbeitnow.py`. For both `tags` and
`job_types`, it accepts an array or an object. Arrays retain their order; objects
use their values in JSON insertion order, which preserves the numeric-key order
used by the observed Arbeitnow response. Only string values are retained. Missing,
null, scalar, and otherwise unsupported values become an empty list.

The normalized `tags` and `job_types` values are concatenated before constructing
the `Job`, preserving the current normalized `Job.tags` contract.

## Source failure isolation

Wrap each top-level `source.fetch()` call in `src/main.py` with an exception boundary.
If an adapter raises unexpectedly, log the source name and exception, then continue
with subsequent sources. Successfully fetched jobs from other sources continue
through deduplication, filtering, judging, persistence, and notification.

This boundary is defensive: adapters remain responsible for their own expected
network and per-company failures. The main loop protects the whole scheduled scan
from an unhandled adapter regression or upstream schema surprise.

## Error handling and observability

The source-level log uses the adapter's `name` when available and its class name as
a fallback. The exception text is included for Actions diagnostics. No retry is
added because adapter requests already control their own request behavior, and an
unbounded pipeline retry could duplicate cost or notifications.

## Tests and verification

Add an Arbeitnow unit test with the observed object-shaped `tags` payload and
array-shaped `job_types`, asserting that all string values are retained in order.
Also cover unsupported/non-string tag values so malformed metadata cannot re-create
the crash.

Add a main-pipeline test in which one source raises while a later source returns a
valid job. Assert that the run continues, the valid job is processed, and the source
failure is logged.

Before pushing to `main`, run:

- `python -m unittest discover -s tests -v`
- `python -m compileall -q src tests`
- `git diff --check`
- `python -m src.main --dry-run` against the live public feeds

After pushing, manually dispatch `Daily job scan` and confirm that the workflow
finishes successfully. The manual run may consume configured LLM calls and send the
normal digest because the workflow has no dry-run input; this is expected for the
production verification requested here.
