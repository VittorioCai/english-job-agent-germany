"""Minimal LLM client. Bring your own key.

Providers (env LLM_PROVIDER): anthropic | openai | deepseek | any OpenAI-compatible
via LLM_BASE_URL. Key in LLM_API_KEY, model override in LLM_MODEL.
"""
import json
import os

import requests

DEFAULTS = {
    "anthropic": ("https://api.anthropic.com", "claude-haiku-4-5-20251001"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "deepseek": ("https://api.deepseek.com", "deepseek-chat"),
}


def complete(prompt: str, max_tokens: int = 1024) -> str:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    api_key = os.environ["LLM_API_KEY"]
    base, model = DEFAULTS.get(provider, (os.environ.get("LLM_BASE_URL", ""), ""))
    base = os.environ.get("LLM_BASE_URL", base)
    model = os.environ.get("LLM_MODEL", model)

    if provider == "anthropic":
        resp = requests.post(
            f"{base}/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    # OpenAI-compatible (openai, deepseek, local, ...)
    resp = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def complete_json(prompt: str, max_tokens: int = 1024):
    """Ask for JSON, tolerate markdown fences."""
    text = complete(prompt, max_tokens).strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.startswith("json") else text
    return json.loads(text.strip())
