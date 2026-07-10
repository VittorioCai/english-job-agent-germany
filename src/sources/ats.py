"""Public ATS feeds (no auth): Greenhouse, Lever, Ashby.

Company list lives in data/companies.yaml — PRs welcome.
Verified endpoints:
  Greenhouse: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
  Lever:      https://api.lever.co/v0/postings/{slug}?mode=json
  Ashby:      https://api.ashbyhq.com/posting-api/job-board/{slug}
"""
import html
import re

import requests

from .base import Job, Source


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _get(url: str):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


class ATSSource(Source):
    name = "ats"

    def __init__(self, companies: list):
        self.companies = companies  # [{name, ats, slug}, ...]

    def fetch(self) -> list:
        jobs = []
        for c in self.companies:
            fn = {"greenhouse": self._greenhouse, "lever": self._lever, "ashby": self._ashby}.get(c["ats"])
            if not fn:
                continue
            try:
                found = fn(c)
                jobs.extend(found)
                print(f"[ats] {c['name']}: {len(found)} jobs")
            except Exception as e:
                print(f"[ats] {c['name']} skipped ({e})")
        return jobs

    def _greenhouse(self, c) -> list:
        data = _get(f"https://boards-api.greenhouse.io/v1/boards/{c['slug']}/jobs?content=true")
        return [Job(
            id=f"greenhouse:{c['slug']}:{j['id']}",
            title=j.get("title", ""),
            company=c["name"],
            location=(j.get("location") or {}).get("name", ""),
            url=j.get("absolute_url", ""),
            description=_strip_html(j.get("content", ""))[:6000],
            source="greenhouse",
        ) for j in data.get("jobs", [])]

    def _lever(self, c) -> list:
        data = _get(f"https://api.lever.co/v0/postings/{c['slug']}?mode=json")
        return [Job(
            id=f"lever:{c['slug']}:{j['id']}",
            title=j.get("text", ""),
            company=c["name"],
            location=(j.get("categories") or {}).get("location", ""),
            url=j.get("hostedUrl", ""),
            description=(j.get("descriptionPlain") or _strip_html(j.get("description", "")))[:6000],
            source="lever",
        ) for j in data]

    def _ashby(self, c) -> list:
        data = _get(f"https://api.ashbyhq.com/posting-api/job-board/{c['slug']}")
        return [Job(
            id=f"ashby:{c['slug']}:{j.get('id', j.get('jobUrl', ''))}",
            title=j.get("title", ""),
            company=c["name"],
            location=j.get("location", ""),
            url=j.get("jobUrl", "") or j.get("applyUrl", ""),
            description=_strip_html(j.get("descriptionHtml", "") or j.get("descriptionPlain", ""))[:6000],
            source="ashby",
        ) for j in data.get("jobs", [])]
