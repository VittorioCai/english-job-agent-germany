"""Cover-letter subagent (CLI). Drafts, never sends.

  python -m src.agents.draft <job-url>            # English letter
  python -m src.agents.draft <job-url> --de       # German letter (mention your level!)
  python -m src.agents.draft --list               # show draftable jobs

Jobs come from data/matches.json (written by the daily run for every digest
job). Output lands in drafts/ as markdown — edit before using, always.
"""
import json
import os
import re
import sys

import yaml

from ..llm import complete

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MATCHES = os.path.join(ROOT, "data", "matches.json")
DRAFTS = os.path.join(ROOT, "drafts")

PROMPT = """Write a cover letter for this application. Requirements:
- Language: {language}
- 250-320 words, 4 paragraphs: hook, fit (mirror the job's own vocabulary),
  proof (one concrete example from the profile), close.
- Honest: never invent experience not in the profile. If the job asks for
  something the profile lacks, address it briefly and positively.
- No clichés ("I am writing to express..."), no flattery filler.
- Output ONLY the letter body, no subject line, no address block.

Applicant profile:
{cv}

Job: {title} at {company}
Posting:
{description}
"""


def load_matches() -> dict:
    try:
        with open(MATCHES, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main(argv):
    matches = load_matches()
    if not argv or argv[0] == "--list":
        if not matches:
            print("No draftable jobs yet — they appear here after each daily run.")
        for url, m in matches.items():
            print(f"{m['score']:>3}  {m['title']} @ {m['company']}\n     {url}")
        return

    url = argv[0]
    lang = "German (the applicant's German is limited — keep it simple and honest)" \
        if "--de" in argv else "English"
    m = matches.get(url)
    if not m:
        sys.exit("URL not found in data/matches.json — run --list to see options.")

    with open(os.path.join(ROOT, "profile.yaml"), encoding="utf-8") as f:
        cv = yaml.safe_load(f).get("cv_summary", "")

    letter = complete(PROMPT.format(language=lang, cv=cv, title=m["title"],
                                    company=m["company"],
                                    description=m["description"][:4000]),
                      max_tokens=800)

    os.makedirs(DRAFTS, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", f"{m['company']}-{m['title']}".lower())[:70]
    path = os.path.join(DRAFTS, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {m['title']} @ {m['company']}\n\n{url}\n\n---\n\n{letter}\n")
    print(f"[draft] saved: {path}\nEdit it before sending — it is a draft, not you.")


if __name__ == "__main__":
    main(sys.argv[1:])
