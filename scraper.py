"""
scraper.py — Scrapes IT/Tech jobs from BDJobs.com and writes to Google Sheets.

Uses BDJobs' internal REST API (no browser needed).
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
# BDJobs API Endpoints
# ---------------------------------------------------------------------------

LIST_URL = (
    "https://gateway.bdjobs.com/recruitment-account-test/api/JobSearch/GetJobSearch"
)
DETAIL_URL = (
    "https://gateway.bdjobs.com/ActtivejobsTest/api/JobSubsystem/jobDetails"
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

# fcatId=8 → IT/Telecommunication category on BDJobs
LIST_PARAMS = {
    "isPro": 1,
    "rpp": 50,
    "pg": 1,
    "fcatId": 8,
}


# ---------------------------------------------------------------------------
# Google Sheets Setup
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "BDJobs Data"


def connect_to_sheet():
    """Authenticate with Google and return the worksheet."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDENTIALS environment variable not set")

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open(SHEET_NAME)
    worksheet = spreadsheet.sheet1
    return worksheet


# ---------------------------------------------------------------------------
# Scraping Functions
# ---------------------------------------------------------------------------


def fetch_jobs_from_list(max_pages=3):
    """Fetch jobs directly from the BDJobs list API."""
    all_jobs = []

    for page in range(1, max_pages + 1):
        params = {**LIST_PARAMS, "pg": page}
        try:
            resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            jobs = data if isinstance(data, list) else data.get("data", [])

            if not jobs:
                break

            all_jobs.extend(jobs)
            print(f"  Page {page}: found {len(jobs)} jobs")
            time.sleep(0.5)

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"Total jobs collected: {len(all_jobs)}")
    return all_jobs


def fetch_job_detail(job_id):
    """Fetch full details for a single job."""
    try:
        resp = requests.get(
            DETAIL_URL,
            params={"jobId": job_id},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def extract_salary(salary_str):
    """Extract min and max salary from a string."""
    if not salary_str or str(salary_str).lower() in ("negotiable", "na", "n/a", "", "none", "0"):
        return "", ""

    salary_str = str(salary_str).replace(",", "")
    numbers = re.findall(r"\d+", salary_str)
    numbers = [int(n) for n in numbers if int(n) > 1000]

    if len(numbers) >= 2:
        return min(numbers), max(numbers)
    elif len(numbers) == 1:
        return numbers[0], numbers[0]
    return "", ""


def parse_job_from_list(job):
    """Convert a list API job object into a row for our spreadsheet."""

    # Get basic fields from list API
    job_title = str(job.get("jobTitle", "") or job.get("JobTitle", "") or "").strip()
    company = str(job.get("companyName", "") or job.get("CompanyName", "") or "").strip()
    location = str(job.get("location", "") or job.get("Location", "") or "Dhaka").strip()
    job_id = str(job.get("Jobid", "") or job.get("jobId", "") or job.get("JobId", "") or "")

    if not job_title:
        return None

    # Try to get salary and skills from detail API
    salary_min = ""
    salary_max = ""
    skills = ""

    if job_id:
        detail = fetch_job_detail(job_id)
        if detail:
            # The real data is nested inside "data" and "common"
            inner = detail.get("data", {}) or {}
            common = detail.get("common", {}) or {}
            if isinstance(inner, list) and inner:
                inner = inner[0]
            if isinstance(inner, dict) and isinstance(common, dict):
                merged = {**inner, **common}
            elif isinstance(inner, dict):
                merged = inner
            elif isinstance(common, dict):
                merged = common
            else:
                merged = {}

            # Debug: print actual fields for first job
            if not hasattr(parse_job_from_list, "_printed"):
                print(f"  Merged fields: {list(merged.keys())}")
                for k, v in merged.items():
                    if v and str(v).strip() and str(v) != "None":
                        print(f"    {k}: {str(v)[:120]}")
                parse_job_from_list._printed = True

            # Try to find salary from merged data
            for key in merged:
                if "salary" in key.lower():
                    sal_val = merged[key]
                    if sal_val:
                        salary_min, salary_max = extract_salary(str(sal_val))
                        if salary_min:
                            break

            # Try to find skills from merged data
            skill_parts = []
            for key in merged:
                if "skill" in key.lower() or "requirement" in key.lower():
                    val = merged[key]
                    if val and isinstance(val, str) and len(val) < 500:
                        skill_parts.append(val.strip())
            if skill_parts:
                skills = ", ".join(skill_parts)

    return {
        "job_title": job_title,
        "company": company,
        "salary_min": str(salary_min),
        "salary_max": str(salary_max),
        "skills": skills,
        "industry": "IT/Telecommunication",
        "location": location if location and location.lower() != "none" else "Dhaka",
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"=== BDJobs Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    # Step 1: Connect to Google Sheet
    print("1. Connecting to Google Sheets...")
    worksheet = connect_to_sheet()

    # Step 2: Get existing job titles to avoid duplicates
    print("2. Checking existing data...")
    existing_data = worksheet.get_all_values()
    existing_titles = set()
    if len(existing_data) > 1:
        for row in existing_data[1:]:
            if row:
                key = f"{row[0]}|{row[1]}".lower().strip()
                existing_titles.add(key)
    print(f"   Existing entries: {len(existing_titles)}")

    # Step 3: Fetch jobs from list API
    print("3. Fetching job listings from BDJobs...")
    jobs = fetch_jobs_from_list(max_pages=3)

    if not jobs:
        print("No jobs found. Exiting.")
        return

    # Step 4: Parse and enrich each job
    print("4. Processing jobs and fetching details...")
    new_rows = []
    for i, job in enumerate(jobs):
        parsed = parse_job_from_list(job)
        if parsed and parsed["job_title"]:
            key = f"{parsed['job_title']}|{parsed['company']}".lower().strip()
            if key not in existing_titles:
                new_rows.append(parsed)
                existing_titles.add(key)

        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(jobs)}")
        time.sleep(0.3)

    print(f"\n   New jobs to add: {len(new_rows)}")

    # Step 5: Write to Google Sheet
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
        print(f"   Added {len(rows_to_add)} new jobs!")
    else:
        print("5. No new jobs to add.")

    print("\nDone!")


if __name__ == "__main__":
    main()
