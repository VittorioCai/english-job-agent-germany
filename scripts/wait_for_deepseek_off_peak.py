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
