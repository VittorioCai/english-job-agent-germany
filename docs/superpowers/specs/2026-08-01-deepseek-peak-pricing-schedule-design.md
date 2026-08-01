# DeepSeek Peak-Pricing Schedule Design

## Goal

Queue the daily job scan at 10:20 Europe/Berlin while ensuring official DeepSeek
API calls do not start during the announced Beijing-time peak windows of
09:00–12:00 and 14:00–18:00.

## Scheduling behavior

Change the GitHub Actions schedule from 11:20 to 10:20 Europe/Berlin. GitHub
scheduled workflows are best-effort and may start later than the configured time,
so 10:20 is the enqueue target rather than a promised delivery time.

Keep the existing non-zero minute to avoid the higher load commonly seen at the
start of an hour.

## DeepSeek off-peak guard

Add a small standard-library Python script that runs immediately before the
pipeline. It reads `LLM_PROVIDER` using the same default as the workflow.

When the provider is not `deepseek`, the script exits immediately. When the
provider is `deepseek`, it converts the current instant to `Asia/Shanghai` and
applies half-open peak windows:

- 09:00 inclusive to 12:00 exclusive
- 14:00 inclusive to 18:00 exclusive

If the current Beijing time is inside a peak window, the script sleeps until five
minutes after that window ends: 12:05 or 18:05. The buffer avoids boundary or clock
alignment ambiguity. If GitHub has already delayed the run into an off-peak window,
the script returns without sleeping.

The guard is a normal workflow step, so it protects both scheduled runs and manual
`workflow_dispatch` runs. It runs before all source fetching and LLM work; this is
more conservative and avoids restructuring the pipeline solely to move the wait
closer to the first model request.

## Failure behavior

Invalid or unavailable IANA timezone data should fail the guard step and stop the
pipeline rather than risk peak-priced calls. Python 3.12 on the GitHub runner
provides `zoneinfo` and the required timezone database.

The script does not retry or alter any DeepSeek API request. Existing source,
model-budget, persistence, and notification behavior remains unchanged.

## Documentation

Update both READMEs to say that GitHub queues the workflow at 10:20
Europe/Berlin, scheduled execution may be delayed, and exact digest delivery is
not guaranteed. Document the DeepSeek peak windows and runtime wait behavior
without claiming an expected arrival range.

## Tests and verification

Add unit tests for both peak windows, their end boundaries, an off-peak interval,
and a non-DeepSeek provider that must not sleep. Update the existing schedule
documentation test to require 10:20 and the revised English and Chinese wording.

Before publishing, run the full unit suite, Python compilation, and
`git diff --check`. Validate the workflow YAML through the existing textual
tests and inspect its rendered structure. After pushing directly to `main`, do
not manually dispatch the production workflow during this change: the new guard
could intentionally hold a runner for hours, and the next scheduled run is the
appropriate end-to-end validation. Inspect that scheduled run after it completes.
