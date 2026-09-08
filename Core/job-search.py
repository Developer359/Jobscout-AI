import os
import json
import warnings
import logging
from datetime import datetime, date
import pandas as pd
from dotenv import load_dotenv
from jobspy import scrape_jobs

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)

load_dotenv()

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../query_cache.json"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../job_results_cache.json"))

MAX_AGE_DAYS = 1
HOURS_OLD = MAX_AGE_DAYS * 24  # jobspy filters server-side by hours

# Focused strictly on the two most trusted and popular sites to avoid broker errors
SITES = ["indeed", "linkedin"]

RESULTS_WANTED_PER_SITE = 15  # per site, per query


def load_and_prepare_queries() -> list[dict]:
    target_file = CACHE_FILE
    if not os.path.exists(target_file):
        target_file = "query_cache.json"

    if not os.path.exists(target_file):
        raise FileNotFoundError(
            f"Cache file 'query_cache.json' not found. Please run 'python Core/query-generation.py' first."
        )

    with open(target_file, "r") as f:
        data = json.load(f)
        queries_data = data.get("queries", [])

    formatted_queries = []
    for item in queries_data[:3]:
        if isinstance(item, dict):
            q = item.get("query", "").strip()
            j_type = item.get("job_type", "Junior").strip()
            if q:
                formatted_queries.append({"query": q, "job_type": j_type})
        elif isinstance(item, str):
            q = item.strip()
            if q:
                formatted_queries.append({"query": q, "job_type": "Junior"})

    return formatted_queries


def days_since(posted) -> int | None:
    """jobspy returns date_posted as a date/Timestamp/NaT -- normalize to an int."""
    if posted is None or pd.isna(posted):
        return None
    if isinstance(posted, datetime):
        posted_date = posted.date()
    elif isinstance(posted, date):
        posted_date = posted
    else:
        try:
            posted_date = pd.to_datetime(posted).date()
        except (ValueError, TypeError):
            return None
    return max((date.today() - posted_date).days, 0)


def safe_str(value, default: str = "") -> str:
    """pandas represents missing values as NaN (a float), not None or ""."""
    if value is None or pd.isna(value):
        return default
    return str(value)


def format_pay(row) -> str:
    min_amt = row.get("min_amount")
    max_amt = row.get("max_amount")
    interval = row.get("interval") or ""
    if pd.isna(min_amt) and pd.isna(max_amt):
        return "Not specified"
    parts = []
    if not pd.isna(min_amt):
        parts.append(f"${int(min_amt):,}")
    if not pd.isna(max_amt) and max_amt != min_amt:
        parts.append(f"${int(max_amt):,}")
    pay_str = " - ".join(parts) if len(parts) > 1 else parts[0]
    return f"{pay_str} / {interval}".strip(" /") if interval else pay_str


def execute_job_search(query_items: list[dict], location: str = "", is_remote: bool = True):
    all_jobs = []
    seen_urls = set()

    print(f"--- Searching {len(query_items)} queries across trusted sites: {SITES} | max age: {MAX_AGE_DAYS} days ---")

    for i, item in enumerate(query_items):
        query = item["query"]
        job_type = item["job_type"]
        print(f"\n[Query {i+1}/{len(query_items)}] [{job_type}] {query}")
        try:
            jobs_df = scrape_jobs(
                site_name=SITES,
                search_term=query,
                location=location,
                is_remote=is_remote,
                results_wanted=RESULTS_WANTED_PER_SITE,
                hours_old=HOURS_OLD,
                country_indeed="USA",
                description_format="markdown",
                linkedin_fetch_description=True,  # Necessary for LinkedIn full descriptions
            )
        except Exception as e:
            print(f"  -> Error on query {i+1}: {e}")
            continue

        if jobs_df is None or jobs_df.empty:
            print("  -> No results returned for this query.")
            continue

        count_for_query = 0
        for _, row in jobs_df.iterrows():
            url = row.get("job_url")
            if not url or pd.isna(url) or url in seen_urls:
                continue

            age_days = days_since(row.get("date_posted"))
            if age_days is not None and age_days > MAX_AGE_DAYS:
                continue

            seen_urls.add(url)
            count_for_query += 1

            title = safe_str(row.get("title"))
            company_name = safe_str(row.get("company"), "Unknown")
            website_name = safe_str(row.get("site"))
            description = safe_str(row.get("description"))[:2000]
            tags = [w for w in title.split() if len(w) > 3]
            pay_info = format_pay(row)

            job_entry = {
                "url": url,
                "title": title,
                "description": description,
                "tags": tags,
                "pay_info": pay_info,
                "company_name": company_name,
                "website_name": website_name,
                "posted_days_ago": age_days,
                "location": safe_str(row.get("location")),
                "job_type": job_type,
                "query_index": i + 1,
                "query_used": query,
            }
            all_jobs.append(job_entry)
            desc_preview = description[:150].replace("\n", " ") + ("..." if len(description) > 150 else "")
            print(f"  [{count_for_query}] [{job_type}] {job_entry['title']}")
            print(f"      Link: {job_entry['url']}")
            print(f"      Description: {desc_preview}")
            print(f"      Tags: {', '.join(tags) if tags else 'None'}")
            print(f"      Pay: {pay_info}")
            print(f"      Company: {company_name}")
            print(f"      Site: {website_name}")

        print(f"  -> {count_for_query} fresh job(s) kept from this query.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"jobs": all_jobs}, f, indent=4, ensure_ascii=False)

    print(f"\nSaved {len(all_jobs)} job(s) (<= {MAX_AGE_DAYS} days old) to job_results_cache.json")
    return all_jobs


if __name__ == "__main__":
    search_queries = load_and_prepare_queries()
    execute_job_search(search_queries)