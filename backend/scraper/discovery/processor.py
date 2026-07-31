import pandas as pd
import os
import re
import logging
from config import OUTPUT_FILE, EXCLUDE_TITLE_KEYWORDS, DAYS_BACK

# Set up logging for this module
logger = logging.getLogger(__name__)


def normalize_company_name(name):
    """Normalize company name for better deduplication."""
    if not name or not isinstance(name, str):
        return ""
    name = name.lower().strip()
    # Remove common corporate suffixes that cause duplicates
    name = re.sub(r'\b(inc|llc|ltd|limited|corp|corporation)\b\.?', '', name)
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def debug_record_fields(record, platform):
    """
    Logs ALL field keys returned by Bright Data for the first record
    of each platform so you can see exactly what fields are available.
    This is only logged once per platform per run.
    """
    if not hasattr(debug_record_fields, "_logged"):
        debug_record_fields._logged = set()
    if platform not in debug_record_fields._logged:
        debug_record_fields._logged.add(platform)
        logger.info(f"\n🔍 DEBUG — All fields returned by Bright Data for [{platform}]:")
        for key, val in record.items():
            logger.info(f"    {key}: {repr(val)[:120]}")
        logger.info("─" * 60)


# ── Fields that may hold the company's own profile page on the same platform ─
# LinkedIn job records: the employer's linkedin.com/company/... page.
# Indeed job records:   the employer's indeed.com/cmp/... page.
# Field names vary across Bright Data schema versions, so try each in order.
_COMPANY_PROFILE_URL_FIELDS = [
    "company_url",
    "company_page_link",
    "company_link",
    "company_linkedin_url",
    "company_indeed_url",
    "employer_url",
]

# ── Known nested paths — e.g. record["employer"]["link"] ─────────────────────
_COMPANY_PROFILE_NESTED_PATHS = [
    ("employer",        "link"),
    ("employer",        "url"),
    ("company_info",    "url"),
    ("company_details", "url"),
]


def extract_company_profile_url(record, platform):
    """
    Pulls the company's profile page URL on the SAME platform the job was
    posted on — linkedin.com/company/... for LinkedIn, indeed.com/cmp/...
    for Indeed. No domain resolution, no second API hop — just whatever
    the job record itself already contains (or a company_id, if that's
    what's returned instead of a direct link).
    Returns "" if nothing usable is found.
    """
    # ── Step 1: Top-level flat fields ────────────────────────────────────
    for field in _COMPANY_PROFILE_URL_FIELDS:
        raw = record.get(field)
        if raw and isinstance(raw, str) and raw.strip():
            return raw.split("?")[0].rstrip("/")

    # ── Step 2: Nested object paths ──────────────────────────────────────
    for parent_key, child_key in _COMPANY_PROFILE_NESTED_PATHS:
        parent = record.get(parent_key)
        if isinstance(parent, dict):
            raw = parent.get(child_key)
            if raw and isinstance(raw, str) and raw.strip():
                return raw.split("?")[0].rstrip("/")

    # ── Step 3: Reconstruct from a company_id, LinkedIn only ─────────────
    if platform == "linkedin":
        company_id = record.get("company_id")
        if company_id:
            return f"https://www.linkedin.com/company/{company_id}"

    return ""


def normalize_record(record, platform):
    """Standardize field names from Bright Data API responses."""

    # Log all fields from the first record per platform — helps debug missing fields
    debug_record_fields(record, platform)

    job_title    = record.get("title") or record.get("job_title", "")
    company_name = record.get("company") or record.get("company_name", "")
    job_location = record.get("location") or record.get("job_location", "")
    url          = record.get("url") or record.get("job_url", "")
    company_profile_url = extract_company_profile_url(record, platform)

    if platform == "linkedin":
        return {
            "job_title":           job_title,
            "company_name":        company_name,
            "company_profile_url": company_profile_url,
            "job_location":        job_location,   # kept internally for dedup only, dropped before CSV export
            "job_url":             url,
            "date_posted":         record.get("posted_at") or record.get("posted_date", ""),
            "platform":            "LinkedIn"
        }
    elif platform == "indeed":
        return {
            "job_title":           job_title,
            "company_name":        company_name,
            "company_profile_url": company_profile_url,
            "job_location":        job_location,   # kept internally for dedup only, dropped before CSV export
            "job_url":             url,
            "date_posted":         record.get("posted_at") or record.get("date_posted_parsed") or record.get("date_posted", ""),
            "platform":            "Indeed"
        }
    return {}

def clean_and_filter(raw_results):
    """Processes, cleans, and deduplicates the raw scraped leads."""
    normalized = []

    for record in raw_results:
        platform = record.get("source_platform", "")
        clean = normalize_record(record, platform)
        clean["search_title"]   = record.get("search_title", "")
        clean["search_country"] = record.get("search_country", "")
        normalized.append(clean)

    df = pd.DataFrame(normalized)

    if df.empty:
        logger.warning("⚠️ No data to process.")
        return df

    logger.info(f"\n📊 Raw records: {len(df)}")

    # Remove empty companies
    df = df[df["company_name"].str.strip() != ""]
    logger.info(f"✅ After removing empty companies: {len(df)}")

    # Filter out excluded HR/Recruiter keywords
    pattern = "|".join([re.escape(k.lower()) for k in EXCLUDE_TITLE_KEYWORDS])
    df = df[~df["job_title"].str.lower().str.contains(pattern, na=False)]
    logger.info(f"✅ After excluding HR/Recruiter titles: {len(df)}")

    # Improve deduplication by adding normalized columns temporarily
    df['_norm_title'] = df['job_title'].astype(str).str.lower().str.strip()
    df['_norm_company'] = df['company_name'].apply(normalize_company_name)
    df['_norm_location'] = df['job_location'].astype(str).str.lower().str.strip()

    df = df.drop_duplicates(subset=["_norm_title", "_norm_company", "_norm_location"])
    logger.info(f"✅ After enhanced deduplication: {len(df)}")

    # Drop temporary columns
    df = df.drop(columns=['_norm_title', '_norm_company', '_norm_location'])

    # Safety-net recency filter: the LinkedIn/Indeed URL params already restrict
    # results to the last DAYS_BACK days, but if a record's date_posted can be
    # parsed and turns out to be older than that window, drop it too. Records
    # whose date can't be parsed are kept rather than discarded.
    before = len(df)
    parsed_dates = pd.to_datetime(df["date_posted"], errors="coerce", utc=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=DAYS_BACK)
    df = df[parsed_dates.isna() | (parsed_dates >= cutoff)]
    logger.info(f"✅ After recency filter (last {DAYS_BACK} days): {len(df)} (removed {before - len(df)})")

    df = df.reset_index(drop=True)

    # ── Final output shape ────────────────────────────────────────────────
    # job_location was only needed internally for deduplication — it's not
    # one of the required output columns, so it's dropped here along with
    # the rename/reorder into the exact columns requested:
    #   Company Name, Company Profile URL, Job Title, Job Posting URL,
    #   Portal, Country, Tier Signal, Date
    df = df.rename(columns={
        "company_name":        "Company Name",
        "company_profile_url": "Company Profile URL",
        "job_title":           "Job Title",
        "job_url":             "Job Posting URL",
        "platform":            "Portal",
        "search_country":      "Country",
        "search_title":        "Tier Signal",   # the job-title query that surfaced this lead
        "date_posted":         "Date",
    })
    df = df[[
        "Company Name", "Company Profile URL", "Job Title",
        "Job Posting URL", "Portal", "Country", "Tier Signal", "Date",
    ]]

    return df

def save_to_csv(df):
    """Saves the final DataFrame to the output CSV file."""
    os.makedirs("output", exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"\n💾 Saved {len(df)} leads to: {OUTPUT_FILE}")
    except PermissionError:
        logger.error(f"\n❌ Permission Denied: Could not save to {OUTPUT_FILE}.")
        logger.error("Please close the file if it is open in Excel or another program.")
        logger.error("The script will continue collecting leads in memory and try to save again on the next pass.")
