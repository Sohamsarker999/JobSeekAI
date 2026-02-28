"""
ai_summary.py — LLM-powered market intelligence via the Groq API.

Features:
  - generate_market_summary()     : executive market brief
  - generate_job_recommendations(): AI job matching
  - analyze_skill_gap()           : skill gap analysis + readiness score
  - estimate_salary()             : AI-powered salary estimator
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL      = "llama-3.3-70b-versatile"
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


def _call_groq(messages: list, max_tokens: int = 512) -> str:
    """Low-level helper: sends messages to Groq and returns text response."""
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ GROQ_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model":       GROQ_MODEL,
        "messages":    messages,
        "temperature": 0.3,
        "max_tokens":  max_tokens,
    }
    try:
        resp = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⚠️ **Request Timed Out** — Please try again."
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "N/A"
        return f"⚠️ **API Error (HTTP {status})** — Check your API key and quota."
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return "⚠️ **AI Unavailable** — Could not connect to Groq. Please try again."


# ---------------------------------------------------------------------------
# FEATURE 1: Market Intelligence Summary
# ---------------------------------------------------------------------------

def _build_prompt(
    top_skills: List[Tuple[str, int]],
    avg_salary: float,
    top_role: str,
    top_industry: str,
) -> str:
    skills_str  = ", ".join(f"{s} ({c})" for s, c in top_skills)
    salary_line = (
        f"• Average offered salary: BDT {avg_salary:,.0f}/month"
        if avg_salary and avg_salary > 0
        else "• Salary data: Most employers list salary as 'Negotiable'"
    )
    return f"""You are a senior labour-market analyst specialising in the
Bangladesh job market.

Based on the following real data extracted from recent job postings on
BDJobs.com (the largest job portal in Bangladesh), write a concise (~200 words)
executive market intelligence brief.

DATA SNAPSHOT
─────────────
- Top in-demand roles/requirements (with frequency): {skills_str}
{salary_line}
- Most common job role: {top_role}
- Dominant industry: {top_industry}

REQUIREMENTS
1. Open with a one-sentence market headline about Bangladesh job market.
2. Highlight 2-3 key hiring trends visible in this data.
3. Comment on which industries are hiring most aggressively.
4. Provide 2 actionable recommendations for job seekers in Bangladesh.
5. Close with a forward-looking outlook (1-2 sentences).

Write in a professional, data-driven tone. Avoid filler phrases.
Be specific to Bangladesh context."""


FALLBACK_MESSAGE = (
    "⚠️ **AI Summary Unavailable**\n\n"
    "Could not generate the market intelligence summary at this time. "
    "Please verify your `GROQ_API_KEY` and try again."
)


def generate_market_summary(
    top_skills: List[Tuple[str, int]],
    salary_metrics: Dict[str, float | None],
    top_role: str,
    top_industry: str,
) -> str:
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ **API Key Missing** — Set `GROQ_API_KEY` to enable AI summaries."

    avg_salary = salary_metrics.get("mean") or 0.0
    prompt     = _build_prompt(top_skills, avg_salary, top_role, top_industry)
    messages   = [
        {
            "role": "system",
            "content": (
                "You are a concise, data-driven labour-market analyst. "
                "Respond only with the requested brief — no preamble."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return _call_groq(messages, max_tokens=512)


# ---------------------------------------------------------------------------
# FEATURE 2: AI-Powered Job Recommendations
# ---------------------------------------------------------------------------

def generate_job_recommendations(
    user_profile: str,
    df: pd.DataFrame,
    top_n: int = 5,
) -> list[dict]:
    if df.empty:
        return [{"error": "No job data available to match against."}]

    sample_df = df.sample(min(80, len(df)), random_state=42).reset_index(drop=True)

    lines = []
    for idx, row in sample_df.iterrows():
        lines.append(
            f"ID:{idx} | {str(row.get('job_title','N/A')).strip()} "
            f"@ {str(row.get('company','N/A')).strip()} | "
            f"Loc:{str(row.get('location','N/A')).strip()} | "
            f"Industry:{str(row.get('industry','N/A')).strip()} | "
            f"Skills:{str(row.get('skills','N/A')).strip()[:120]}"
        )

    prompt = f"""You are a career advisor specialising in the Bangladesh job market.

CANDIDATE PROFILE:
\"\"\"{user_profile}\"\"\"

AVAILABLE JOBS:
{chr(10).join(lines)}

Select the TOP {top_n} best-matching jobs. Return ONLY a valid JSON array:
[
  {{"job_id": <int>, "match_score": <0-100>, "reason": "<1-2 sentences>"}},
  ...
]"""

    messages = [
        {
            "role": "system",
            "content": "You are a precise career-matching engine. Reply with valid JSON only.",
        },
        {"role": "user", "content": prompt},
    ]

    raw = _call_groq(messages, max_tokens=900)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        matches = json.loads(clean.strip())
    except Exception:
        return [{"error": f"Could not parse AI response:\n\n{raw}"}]

    if not isinstance(matches, list):
        return [{"error": "Unexpected response format. Please try again."}]

    results = []
    for rank, match in enumerate(matches[:top_n], start=1):
        job_id = match.get("job_id")
        try:
            row = sample_df.loc[int(job_id)]
        except (KeyError, TypeError, ValueError):
            continue
        results.append({
            "rank":        rank,
            "job_title":   str(row.get("job_title",  "N/A")).strip(),
            "company":     str(row.get("company",    "N/A")).strip(),
            "location":    str(row.get("location",   "N/A")).strip(),
            "industry":    str(row.get("industry",   "N/A")).strip(),
            "experience":  str(row.get("skills",     "N/A")).strip()[:120],
            "deadline":    str(row.get("deadline",   "")).strip(),
            "match_score": int(match.get("match_score", 0)),
            "reason":      str(match.get("reason", "")).strip(),
        })

    if not results:
        return [{"error": "AI returned matches but none mapped to real jobs. Try again."}]
    return results


# ---------------------------------------------------------------------------
# FEATURE 3: Skill Gap Analyzer
# ---------------------------------------------------------------------------

def _extract_market_skills(df: pd.DataFrame, top_n: int = 40) -> List[str]:
    from collections import Counter
    import re

    STOPWORDS = {
        "the","and","or","in","of","to","a","an","is","are","for","with",
        "on","at","by","as","be","will","we","you","not","this","that",
        "our","from","have","has","experience","required","minimum","maximum",
        "years","year","job","work","candidate","applicant","position","role",
        "company","team","good","strong","excellent","knowledge","ability",
        "skill","skills","must","should","prefer","preferred","graduate",
        "university","degree","education","male","female","both","any","all",
        "other","please","apply","salary","negotiable","attractive","package",
        "bangladesh","dhaka","chittagong","sylhet",
    }

    col = "skills" if "skills" in df.columns else None
    if col is None:
        return []

    all_tokens: list[str] = []
    for text in df[col].dropna().astype(str):
        tokens = re.split(r"[,/|;\n]+", text.lower())
        for token in tokens:
            token = token.strip()
            if 2 <= len(token) <= 40 and token not in STOPWORDS:
                all_tokens.append(token)

    return [skill for skill, _ in Counter(all_tokens).most_common(top_n)]


def analyze_skill_gap(user_profile: str, df: pd.DataFrame) -> dict:
    if df.empty:
        return {"error": "No job data available."}
    if not user_profile.strip():
        return {"error": "Please enter your skills and background first."}

    market_skills     = _extract_market_skills(df, top_n=40)
    if not market_skills:
        return {"error": "Could not extract market skills from dataset."}

    top_roles_str     = ", ".join(df["job_title"].value_counts().head(10).index.tolist())
    top_industries_str= ", ".join(df["industry"].value_counts().head(6).index.tolist())
    market_skills_str = ", ".join(market_skills)

    prompt = f"""You are a senior career coach specialising in the Bangladesh job market.

CANDIDATE PROFILE:
\"\"\"{user_profile}\"\"\"

LIVE MARKET DATA (from {len(df)} real BDJobs postings):
- Most demanded skills: {market_skills_str}
- Top hiring roles: {top_roles_str}
- Top industries: {top_industries_str}

Return ONLY a valid JSON object (no markdown fences):
{{
  "readiness_score": <int 0-100>,
  "matched_skills": [<up to 8 strings>],
  "missing_critical": [
    {{"skill":"<name>","reason":"<1 sentence>","how_to_learn":"<free resource>"}}
  ],
  "missing_optional": [<up to 5 strings>],
  "strengths": [<up to 4 strings>],
  "top_roles": [<3 role titles from market data>],
  "summary": "<2-3 sentence narrative>"
}}"""

    messages = [
        {
            "role": "system",
            "content": "You are a precise skill gap analysis engine. Reply with valid JSON only.",
        },
        {"role": "user", "content": prompt},
    ]

    raw = _call_groq(messages, max_tokens=1200)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
    except Exception:
        return {"error": f"Could not parse AI response:\n\n{raw}"}

    for key in ["readiness_score","matched_skills","missing_critical",
                "missing_optional","strengths","top_roles","summary"]:
        if key not in result:
            result[key] = [] if key != "readiness_score" else 50

    score = int(result.get("readiness_score", 50))
    if score >= 80:
        result["score_label"] = "Strong"
        result["score_color"] = "#16a34a"
    elif score >= 60:
        result["score_label"] = "Good"
        result["score_color"] = "#2563eb"
    elif score >= 40:
        result["score_label"] = "Developing"
        result["score_color"] = "#d97706"
    else:
        result["score_label"] = "Early Stage"
        result["score_color"] = "#dc2626"

    result["error"] = None
    return result


# ---------------------------------------------------------------------------
# FEATURE 4: AI-Powered Salary Estimator  ◄─ NEW
# ---------------------------------------------------------------------------

def estimate_salary(
    job_title: str,
    industry: str,
    experience_level: str,
    years_of_experience: int,
    location: str,
    education: str,
    df: pd.DataFrame,
) -> dict:
    """
    Use Groq AI to estimate a realistic BDT salary range for the given
    profile, grounded in live scraped market data for context.

    Returns a dict with keys:
        min_salary       : int   (BDT/month)
        max_salary       : int   (BDT/month)
        median_salary    : int   (BDT/month)
        currency         : str   "BDT"
        confidence       : str   "High" | "Medium" | "Low"
        confidence_color : str   hex
        reasoning        : str   paragraph explaining the estimate
        market_context   : str   how this role compares to the market
        negotiation_tips : list[str]
        factors_up       : list[str]   things that push salary higher
        factors_down     : list[str]   things that push salary lower
        error            : str | None
    """
    if not job_title.strip():
        return {"error": "Please select a job role."}

    # Pull market context from scraped data to ground the AI's answer
    total_jobs    = len(df)
    role_count    = int((df["job_title"] == job_title).sum()) if not df.empty else 0
    industry_jobs = int((df["industry"]  == industry).sum())  if not df.empty else 0
    top_companies = (
        df[df["industry"] == industry]["company"]
        .value_counts().head(5).index.tolist()
        if not df.empty else []
    )
    top_cos_str   = ", ".join(top_companies) if top_companies else "N/A"

    prompt = f"""You are a senior compensation analyst and HR consultant
specialising exclusively in the Bangladesh job market.

A user wants a salary estimate for the following profile:

PROFILE
───────
Job Title          : {job_title}
Industry           : {industry}
Experience Level   : {experience_level}
Years of Experience: {years_of_experience} year(s)
Location           : {location}
Education          : {education}

LIVE MARKET CONTEXT (from {total_jobs} real BDJobs.com postings scraped today):
- Postings for this exact role      : {role_count}
- Postings in this industry         : {industry_jobs}
- Top hiring companies in industry  : {top_cos_str}
- Note: BDJobs hides most salaries — this estimate uses your expert knowledge
  of Bangladesh compensation norms, cross-referenced with the market context above.

TASK — Return ONLY a valid JSON object (no markdown fences, no extra text):
{{
  "min_salary"       : <integer, monthly BDT, realistic floor>,
  "max_salary"       : <integer, monthly BDT, realistic ceiling>,
  "median_salary"    : <integer, monthly BDT, most likely/typical>,
  "confidence"       : "<High|Medium|Low>",
  "reasoning"        : "<3-4 sentences explaining the estimate, specific to BD market>",
  "market_context"   : "<2 sentences: how this role/salary compares to BD market overall>",
  "negotiation_tips" : [<3 specific, actionable negotiation tips for BD job market>],
  "factors_up"       : [<3 things that would push this salary higher>],
  "factors_down"     : [<3 things that would push this salary lower>]
}}

RULES:
- All salary values must be realistic monthly BDT figures for Bangladesh
- Entry level IT in Dhaka typically BDT 20,000–50,000
- Mid level IT in Dhaka typically BDT 50,000–120,000
- Senior level IT in Dhaka typically BDT 100,000–250,000+
- NGO/Development sector: typically 30-50% above private sector
- Banking sector: typically 20-40% above average
- Garments/Manufacturing: typically below average
- Outside Dhaka: typically 15-25% lower
- Be realistic and specific — not overly optimistic
- confidence: High if role+industry is common, Low if niche/rare"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise Bangladesh compensation analyst. "
                "Reply with a valid JSON object only — no prose, no markdown."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    raw = _call_groq(messages, max_tokens=900)

    # Parse JSON
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.lower().startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
    except Exception:
        return {"error": f"Could not parse AI response:\n\n{raw}"}

    # Validate numeric fields
    for key in ("min_salary", "max_salary", "median_salary"):
        if key not in result:
            return {"error": f"AI response missing '{key}'. Please try again."}
        try:
            result[key] = int(result[key])
        except (ValueError, TypeError):
            return {"error": f"Invalid salary value for '{key}'. Please try again."}

    # Ensure logical ordering
    result["min_salary"]    = min(result["min_salary"],    result["median_salary"])
    result["max_salary"]    = max(result["max_salary"],    result["median_salary"])
    result["currency"]      = "BDT"

    # Confidence colour
    conf = result.get("confidence", "Medium")
    result["confidence_color"] = (
        "#16a34a" if conf == "High" else
        "#d97706" if conf == "Medium" else
        "#dc2626"
    )

    # Ensure list fields exist
    for key in ("negotiation_tips", "factors_up", "factors_down"):
        if key not in result or not isinstance(result[key], list):
            result[key] = []

    result["error"] = None
    return result
