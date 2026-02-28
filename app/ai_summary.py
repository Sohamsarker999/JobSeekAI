"""
ai_summary.py — LLM-powered market intelligence via the Groq API.

Constructs a dynamic prompt from live analytics and returns an
executive-level market insight summary.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT = 30


def _get_api_key() -> str | None:
    """Retrieve the Groq API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------


def _build_prompt(
    top_skills: List[Tuple[str, int]],
    avg_salary: float,
    top_role: str,
    top_industry: str,
) -> str:
    """Create a structured prompt for the LLM from analytical summaries."""
    skills_str = ", ".join(f"{s} ({c})" for s, c in top_skills)

    salary_line = ""
    if avg_salary and avg_salary > 0:
        salary_line = f"• Average offered salary: BDT {avg_salary:,.0f}/month"
    else:
        salary_line = "• Salary data: Most employers list salary as 'Negotiable'"

    return f"""You are a senior labour-market analyst specialising in the
Bangladesh job market.

Based on the following real data extracted from recent job postings on
BDJobs.com (the largest job portal in Bangladesh), write a concise (~200 words)
executive market intelligence brief.

DATA SNAPSHOT
─────────────
• Top in-demand roles/requirements (with frequency): {skills_str}
{salary_line}
• Most common job role: {top_role}
• Dominant industry: {top_industry}

REQUIREMENTS
1. Open with a one-sentence market headline about Bangladesh job market.
2. Highlight 2-3 key hiring trends visible in this data.
3. Comment on which industries are hiring most aggressively.
4. Provide 2 actionable recommendations for job seekers in Bangladesh.
5. Close with a forward-looking outlook (1-2 sentences).

Write in a professional, data-driven tone suitable for an executive
dashboard. Avoid filler phrases. Be specific to Bangladesh context."""


# ---------------------------------------------------------------------------
# API Call
# ---------------------------------------------------------------------------

FALLBACK_MESSAGE = (
    "⚠️ **AI Summary Unavailable**\n\n"
    "Could not generate the market intelligence summary at this time. "
    "Please verify your `GROQ_API_KEY` environment variable is set and try again.\n\n"
    "You can still explore the analytics above."
)


def generate_market_summary(
    top_skills: List[Tuple[str, int]],
    salary_metrics: Dict[str, float | None],
    top_role: str,
    top_industry: str,
) -> str:
    """Call the Groq API and return a market-insight paragraph."""
    api_key = _get_api_key()
    if not api_key:
        return (
            "⚠️ **API Key Missing**\n\n"
            "Set the `GROQ_API_KEY` environment variable to enable "
            "AI-powered market summaries."
        )

    avg_salary = salary_metrics.get("mean") or 0.0
    prompt = _build_prompt(top_skills, avg_salary, top_role, top_industry)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise, data-driven labour-market analyst. "
                    "Respond only with the requested brief — no preamble."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return (
            "⚠️ **Request Timed Out**\n\n"
            "The AI service took too long to respond. Please try again shortly."
        )
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "N/A"
        return (
            f"⚠️ **API Error (HTTP {status})**\n\n"
            "Could not retrieve the AI summary. Check your API key and quota."
        )
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return FALLBACK_MESSAGE
