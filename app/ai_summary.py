"""
ai_summary.py — LLM-powered market intelligence via the Groq API.

Constructs a dynamic prompt from live analytics and returns an
executive-level market insight summary.

Works with both:
  • Streamlit Cloud secrets (st.secrets)
  • Local .env / environment variables
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # fast, high-quality model on Groq
REQUEST_TIMEOUT = 30  # seconds


def _get_api_key() -> str | None:
    """Retrieve the Groq API key from Streamlit secrets or environment.

    Priority:
      1. st.secrets["GROQ_API_KEY"]  (Streamlit Cloud)
      2. os.environ["GROQ_API_KEY"]  (local .env / export)
    """
    # Try Streamlit secrets first (used on Streamlit Cloud)
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass

    # Fall back to environment variable (local development)
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

    return f"""You are a senior labour-market analyst specialising in the 
Bangladesh technology sector.

Based on the following real data extracted from recent job postings, write a 
concise (~200 words) executive market intelligence brief.

DATA SNAPSHOT
─────────────
• Top in-demand skills (with frequency): {skills_str}
• Average offered salary: BDT {avg_salary:,.0f}/month
• Most common job role: {top_role}
• Dominant industry: {top_industry}

REQUIREMENTS
1. Open with a one-sentence market headline.
2. Highlight 2-3 key talent-demand trends.
3. Comment on salary competitiveness relative to the region.
4. Provide 2 actionable recommendations for job seekers.
5. Close with a forward-looking outlook (1-2 sentences).

Write in a professional, data-driven tone suitable for an executive 
dashboard. Avoid filler phrases. Be specific."""


# ---------------------------------------------------------------------------
# API Call
# ---------------------------------------------------------------------------

FALLBACK_MESSAGE = (
    "⚠️ **AI Summary Unavailable**\n\n"
    "Could not generate the market intelligence summary at this time. "
    "Please verify your `GROQ_API_KEY` environment variable is set and try again.\n\n"
    "You can still explore the skill and salary analytics above."
)


def generate_market_summary(
    top_skills: List[Tuple[str, int]],
    salary_metrics: Dict[str, float | None],
    top_role: str,
    top_industry: str,
) -> str:
    """Call the Groq API and return a market-insight paragraph.

    Returns a graceful fallback message on any failure.
    """
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
