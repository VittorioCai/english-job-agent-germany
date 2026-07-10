"""Daily digest via SMTP (Gmail app password works out of the box)."""
import os
import smtplib
from email.mime.text import MIMEText

CARD = """
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:12px 0;font-family:sans-serif">
  <div style="font-size:16px;font-weight:bold">
    <a href="{url}" style="color:#1a73e8;text-decoration:none">{title}</a>
    <span style="float:right;color:{score_color}">{score}/100</span>
  </div>
  <div style="color:#555;margin:4px 0">{company} · {location} · working language: {lang} · German needed: {german}</div>
  <div style="margin:6px 0">{summary}</div>
  <div style="color:#888;font-size:13px">Evidence: “{evidence}”</div>
  {flags}
</div>"""


def _card(job, j):
    score = j["match_score"]
    flags = ""
    if j["red_flags"]:
        flags = ('<div style="color:#c5221f;font-size:13px;margin-top:4px">⚠ '
                 + " · ".join(j["red_flags"]) + "</div>")
    return CARD.format(
        url=job.url, title=job.title, score=score,
        score_color="#188038" if score >= 70 else "#e37400",
        company=job.company, location=job.location,
        lang=j.get("working_language", "?"), german=j.get("german_required", "?"),
        summary=j.get("summary", ""), evidence=j.get("evidence", "")[:200], flags=flags,
    )


def send_digest(top: list, near_misses: list, stats: dict):
    """top / near_misses: [(job, judgment)]"""
    parts = [f"<p style='font-family:sans-serif;color:#555'>Scanned {stats['total']} jobs · "
             f"{stats['gated']} passed rule filters · {stats['judged']} judged by LLM</p>"]
    if top:
        parts.append("<h2 style='font-family:sans-serif'>🎯 Today's matches</h2>")
        parts += [_card(job, j) for job, j in top]
    else:
        parts.append("<p style='font-family:sans-serif'>No strong matches today.</p>")
    if near_misses:
        parts.append("<h3 style='font-family:sans-serif;color:#888'>Close, but filtered out</h3>")
        parts += [_card(job, j) for job, j in near_misses]

    msg = MIMEText("".join(parts), "html")
    msg["Subject"] = f"[no-german-required] {len(top)} matches · {stats['total']} jobs scanned"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ.get("MAIL_TO", os.environ["SMTP_USER"])

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    print(f"[email] digest sent to {msg['To']}")
