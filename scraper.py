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
    "rpp": 50,       # results per page (max 50)
    "pg": 1,
    "fcatId": 8,     # IT/Telecom category
}


# ---------------------------------------------------------------------------
# Google Sheets Setup
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "BDJobs Data"  # must match the sheet you created


def connect_to_sheet():
    """Authenticate with Google and return the worksheet."""
    # GitHub Actions stores the JSON key as a secret (string)
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


def fetch_job_ids(max_pages=3):
    """Fetch job IDs from the BDJobs list API.

    max_pages=3 → up to 150 jobs (50 per page). Keep it small to be polite.
    """
    job_ids = []

    for page in range(1, max_pages + 1):
        params = {**LIST_PARAMS, "pg": page}
        try:
            resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # The API returns a list of job objects
            jobs = data if isinstance(data, list) else data.get("data", [])

            if not jobs:
                break

            for job in jobs:
                job_id = job.get("jobId") or job.get("JobId") or job.get("id")
                if job_id:
                    job_ids.append(str(job_id))

            print(f"  Page {page}: found {len(jobs)} jobs")
            time.sleep(0.5)  # be polite

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"Total job IDs collected: {len(job_ids)}")
    return job_ids


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
    except Exception as e:
        print(f"  Could not fetch job {job_id}: {e}")
        return None


def extract_salary(salary_str):
    """Try to extract min and max salary from a salary string.

    Examples:
      "Tk. 25000 - 40000"  → (25000, 40000)
      "Negotiable"         → ("", "")
    """
    if not salary_str or salary_str.lower() in ("negotiable", "na", "n/a", ""):
        return "", ""

    numbers = re.findall(r"[\d,]+", salary_str.replace(",", ""))
    numbers = [int(n) for n in numbers if n.isdigit()]

    if len(numbers) >= 2:
        return min(numbers), max(numbers)
    elif len(numbers) == 1:
        return numbers[0], numbers[0]
    return "", ""


def extract_skills(detail):
    """Extract skills from job detail — checks multiple possible fields."""
    # BDJobs stores skills in different fields depending on the listing
    candidates = [
        detail.get("skills", ""),
        detail.get("Skills", ""),
        detail.get("otherSkills", ""),
        detail.get("OtherSkills", ""),
        detail.get("additionalRequirements", ""),
    ]

    skills = set()
    for field in candidates:
        if field and isinstance(field, str):
            # Split by common delimiters
            for part in re.split(r"[,;•·\n]", field):
                cleaned = part.strip().strip("-").strip()
                if cleaned and len(cleaned) < 50:  # skip long sentences
                    skills.add(cleaned)

    return ", ".join(sorted(skills)) if skills else ""


def parse_job(detail):
    """Convert raw API detail into a clean row for our spreadsheet."""
    if not detail:
        return None

    salary_str = (
        detail.get("salary", "")
        or detail.get("Salary", "")
        or detail.get("salaryRange", "")
        or ""
    )
    salary_min, salary_max = extract_salary(salary_str)

    job_title = (
        detail.get("jobTitle", "")
        or detail.get("JobTitle", "")
        or detail.get("jobtitle", "")
        or ""
    ).strip()

    company = (
        detail.get("companyName", "")
        or detail.get("CompanyName", "")
        or detail.get("company", "")
        or ""
    ).strip()

    location = (
        detail.get("jobLocation", "")
        or detail.get("JobLocation", "")
        or detail.get("location", "")
        or ""
    ).strip()

    industry = (
        detail.get("industry", "")
        or detail.get("Industry", "")
        or detail.get("functionalCategory", "")
        or ""
    ).strip()

    skills = extract_skills(detail)

    return {
        "job_title": job_title,
        "company": company,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "skills": skills,
        "industry": industry if industry else "IT/Telecommunication",
        "location": location if location else "Dhaka",
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
    if len(existing_data) > 1:  # has data beyond headers
        for row in existing_data[1:]:
            if row:
                # Unique key = job_title + company
                key = f"{row[0]}|{row[1]}".lower().strip()
                existing_titles.add(key)
    print(f"   Existing entries: {len(existing_titles)}")

    # Step 3: Fetch job IDs
    print("3. Fetching job listings from BDJobs...")
    job_ids = fetch_job_ids(max_pages=3)

    if not job_ids:
        print("No jobs found. Exiting.")
        return

    # Step 4: Fetch details and build rows
    print("4. Fetching job details...")
    new_rows = []
    for i, job_id in enumerate(job_ids):
        detail = fetch_job_detail(job_id)
        if detail:
            parsed = parse_job(detail)
            if parsed and parsed["job_title"]:
                key = f"{parsed['job_title']}|{parsed['company']}".lower().strip()
                if key not in existing_titles:
                    new_rows.append(parsed)
                    existing_titles.add(key)

        # Progress + be polite
        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(job_ids)}")
        time.sleep(0.3)

    print(f"\n   New jobs to add: {len(new_rows)}")

    # Step 5: Write to Google Sheet
    if new_rows:
        print("5. Writing to Google Sheets...")
        rows_to_add = [
            [
                r["job_title"],
                r["company"],
                str(r["salary_min"]),
                str(r["salary_max"]),
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
