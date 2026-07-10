"""Application tracker CLI.

  python -m src.track add <job-url> [applied|interview|offer|rejected] [note...]
  python -m src.track list
  python -m src.track stats

Tracked URLs are excluded from future digests automatically.
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "applications.json")
STATUSES = ["applied", "interview", "offer", "rejected"]


def load() -> dict:
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(apps: dict):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)


def tracked_urls() -> set:
    return set(load().keys())


def main(argv):
    apps = load()
    cmd = argv[0] if argv else "list"

    if cmd == "add":
        if len(argv) < 2:
            sys.exit("usage: python -m src.track add <job-url> [status] [note...]")
        url = argv[1]
        status = argv[2] if len(argv) > 2 else "applied"
        if status not in STATUSES:
            sys.exit(f"status must be one of {STATUSES}")
        entry = apps.get(url, {"first_tracked": str(date.today())})
        entry["status"] = status
        entry["updated"] = str(date.today())
        if len(argv) > 3:
            entry["note"] = " ".join(argv[3:])
        apps[url] = entry
        save(apps)
        print(f"[track] {status}: {url}")

    elif cmd == "list":
        if not apps:
            print("No tracked applications yet. Add one: python -m src.track add <url>")
            return
        for url, e in sorted(apps.items(), key=lambda x: x[1].get("updated", ""), reverse=True):
            note = f" — {e['note']}" if e.get("note") else ""
            print(f"[{e['status']:9}] {e.get('updated', '')} {url}{note}")

    elif cmd == "stats":
        counts = {}
        for e in apps.values():
            counts[e["status"]] = counts.get(e["status"], 0) + 1
        total = len(apps)
        print(f"{total} applications tracked")
        for s in STATUSES:
            if counts.get(s):
                print(f"  {s:10} {counts[s]}")

    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
