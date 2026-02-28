"""
scraper.py — Scrapes jobs from BDJobs.com and writes to Google Sheets.

Uses BDJobs' internal REST API (list endpoint only).
Designed to run daily via GitHub Actions.

DISCLAIMER: For educational and portfolio purposes only.
"""

import json
import os
import re
import time
from datetime import datetime

import gspread
import requests
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# BDJobs API
# ---------------------------------------------------------------------------

LIST_URL = (
    "https://gateway.bdjobs.com/recruitment-account-test/api/JobSearch/GetJobSearch"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://bdjobs.com/",
}

# Category IDs on BDJobs
CATEGORIES = {
    8: "IT/Telecommunication",
    2: "Bank/Financial",
    10: "Engineering",
    3: "Marketing/Sales",
    12: "NGO/Development",
    1: "Accounting/Finance",
    6: "Education/Training",
    9: "Healthcare/Medical",
    4: "HR/Admin",
    7: "Garments/Textile",
}

# ---------------------------------------------------------------------------
# Industry Detection from Job Title / Education / Company
# ---------------------------------------------------------------------------

INDUSTRY_KEYWORDS = {
    "IT/Telecommunication": [
        "software", "developer", "programmer", "IT ", "flutter", "react",
        "python", "java", "frontend", "backend", "full stack", "fullstack",
        "devops", "data engineer", "data scien", "machine learning", "AI ",
        "cloud", "network", "system admin", "cyber", "web ", "app ",
        "mern", "node", "database", "telecom",
    ],
    "Bank/Financial": [
        "bank", "banking", "loan", "credit", "finance", "treasury",
        "investment", "insurance", "microfinance", "accounts", "accounting",
        "audit", "tax", "vat", "cashier",
    ],
    "Engineering": [
        "engineer", "civil", "mechanical", "electrical", "architect",
        "construction", "structural", "surveyor", "autocad", "project eng",
        "site eng", "design eng",
    ],
    "Marketing/Sales": [
        "marketing", "sales", "brand", "digital market", "seo",
        "social media", "content", "advertising", "promotion",
        "business develop", "bdm", "area manager", "regional manager",
        "territory", "merchandis",
    ],
    "NGO/Development": [
        "ngo", "development", "humanitarian", "relief", "undp",
        "unicef", "project officer", "field officer", "coordinator",
        "community", "volunteer", "social",
    ],
    "Healthcare/Medical": [
        "medical", "doctor", "nurse", "hospital", "pharma", "health",
        "diagnostic", "lab ", "laboratory", "patholog", "radiolog",
        "technologist",
    ],
    "Education/Training": [
        "teacher", "lecturer", "professor", "trainer", "instructor",
        "education", "school", "university", "academic", "tutor",
        "training",
    ],
    "Garments/Textile": [
        "garment", "textile", "knitting", "dyeing", "washing",
        "sewing", "fabric", "apparel", "sweater", "fashion",
        "merchandiser",
    ],
    "HR/Admin": [
        "hr ", "human resource", "admin", "receptionist", "front desk",
        "office manage", "executive assist", "personal assist",
    ],
    "Accounting/Finance": [
        "accountant", "accounts officer", "bookkeep", "payroll",
        "financial analyst",
    ],
}


def detect_industry(job_title, education="", company=""):
    """Detect industry from job title, education and company name."""
    text = f"{job_title} {education} {company}".lower()

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return industry

    return "General/Other"


# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "BDJobs Data"


def connect_to_sheet():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDENTIALS environment variable not set")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def fetch_jobs(category_id, max_pages=2):
    """Fetch jobs from a specific BDJobs category."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        params = {"isPro": 1, "rpp": 50, "pg": page, "fcatId": category_id}
        try:
            resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            jobs = data if isinstance(data, list) else data.get("data", [])
            if not jobs:
                break
            all_jobs.extend(jobs)
            print(f"    Page {page}: {len(jobs)} jobs")
            time.sleep(0.5)
        except Exception as e:
            print(f"    Error page {page}: {e}")
            break

    return all_jobs


def parse_job(job):
    """Extract fields and detect industry from job content."""
    job_title = str(job.get("jobTitle", "") or "").strip()
    company = str(job.get("companyName", "") or "").strip()
    location = str(job.get("location", "") or "").strip()
    experience = str(job.get("experience", "") or "").strip()
    education = str(job.get("eduRec", "") or "").strip()
    publish_date = str(job.get("publishDate", "") or "").strip()

    if not job_title or job_title.lower() == "none":
        return None

    # Detect industry from job content
    industry = detect_industry(job_title, education, company)

    # Build skills from experience + education
    skills_parts = []
    if experience and experience.lower() != "none":
        skills_parts.append(f"Experience: {experience}")
    if education and education.lower() != "none":
        # Clean HTML tags from education
        clean_edu = re.sub(r"<[^>]+>", "", education).strip()
        if clean_edu:
            skills_parts.append(f"Education: {clean_edu}")
    skills = ", ".join(skills_parts)

    # Clean location
    if not location or location.lower() == "none":
        location = "Dhaka"

    # Parse date
    date_str = datetime.now().strftime("%Y-%m-%d")
    if publish_date and publish_date != "None":
        try:
            dt = datetime.fromisoformat(publish_date.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    return {
        "job_title": job_title,
        "company": company,
        "salary_min": "",
        "salary_max": "",
        "skills": skills,
        "industry": industry,
        "location": location,
        "date_scraped": date_str,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"=== BDJobs Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    print("1. Connecting to Google Sheets...")
    worksheet = connect_to_sheet()

    print("2. Checking existing data...")
    existing_data = worksheet.get_all_values()
    existing_keys = set()
    if len(existing_data) > 1:
        for row in existing_data[1:]:
            if row and len(row) >= 2:
                key = f"{row[0]}|{row[1]}".lower().strip()
                existing_keys.add(key)
    print(f"   Existing entries: {len(existing_keys)}")

    print("3. Fetching jobs from BDJobs...")
    all_jobs = []
    seen_ids = set()
    for cat_id, cat_name in CATEGORIES.items():
        print(f"  [{cat_name}]")
        jobs = fetch_jobs(cat_id, max_pages=2)
        # Deduplicate across categories
        for job in jobs:
            jid = job.get("Jobid") or job.get("jobId") or id(job)
            if jid not in seen_ids:
                seen_ids.add(jid)
                all_jobs.append(job)
        print(f"    Unique so far: {len(all_jobs)}")
    print(f"   Total unique jobs: {len(all_jobs)}")

    print("4. Processing...")
    new_rows = []
    industry_counts = {}
    for job in all_jobs:
        parsed = parse_job(job)
        if parsed:
            key = f"{parsed['job_title']}|{parsed['company']}".lower().strip()
            if key not in existing_keys:
                new_rows.append(parsed)
                existing_keys.add(key)
                # Count industries
                ind = parsed["industry"]
                industry_counts[ind] = industry_counts.get(ind, 0) + 1

    print(f"   New unique jobs: {len(new_rows)}")
    print(f"   Industry breakdown:")
    for ind, cnt in sorted(industry_counts.items(), key=lambda x: -x[1]):
        print(f"     {ind}: {cnt}")

    if new_rows:
        print("5. Writing to Google Sheets...")
        rows_to_add = [
            [
                r["job_title"],
                r["company"],
                r["salary_min"],
                r["salary_max"],
                r["skills"],
                r["industry"],
                r["location"],
                r["date_scraped"],
            ]
            for r in new_rows
        ]
        worksheet.append_rows(rows_to_add, value_input_option="RAW")
        print(f"   ✅ Added {len(rows_to_add)} new jobs!")
    else:
        print("5. No new jobs to add.")

    print("\nDone!")


if __name__ == "__main__":
    main()
