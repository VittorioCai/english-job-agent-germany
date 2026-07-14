"""Company-intel subagent: one short briefing per company, cached forever.

Adds context to digest cards: what the company does, scale, working-language
culture, and 2-3 talking points for an application. Knowledge comes from the
LLM's training data + the job posting itself — treat as orientation, verify
before interviews.
"""
import json
import os

from ..llm import complete_json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "company_intel.json")

PROMPT = """Brief a student job applicant on this company, in strict JSON:

{{
  "what": "<one sentence: what the company does>",
  "scale": "<size/stage, e.g. 'DAX corporate, ~100k employees' or 'Series B startup, ~200 people'>",
  "language_culture": "<what is known about English vs German as working language; 'unknown' if unsure>",
  "talking_points": ["<2-3 specific angles a supply-chain/data student could mention when applying>"]
}}

Rules: be factual and terse. If you are not confident about a fact, write "unknown"
rather than guessing. Use the job posting below as additional evidence.

Company: {company}
Job posting excerpt:
{excerpt}
"""


def _load() -> dict:
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(cache: dict):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)


def briefing(company: str, jd_excerpt: str) -> dict:
    """Cached: each company costs one LLM call ever."""
    cache = _load()
    if company in cache:
        return cache[company]
    try:
        result = complete_json(PROMPT.format(company=company, excerpt=jd_excerpt[:2500]))
    except Exception as e:
        print(f"[intel] {company} failed: {e}")
        return {}
    cache[company] = result
    _save(cache)
    print(f"[intel] briefed: {company}")
    return result
