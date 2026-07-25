import pandas as pd
import os
import re
import logging
import urllib.parse
from datetime import datetime, timezone
from config import OUTPUT_FILE, EXCLUDE_TITLE_KEYWORDS, DAYS_BACK

from dotenv import load_dotenv

# Set up logging for this module
logger = logging.getLogger(__name__)

# Ensure backend/.env environment variables are loaded
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_env_path = os.path.join(base_dir, "..", "..", ".env")
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)
else:
    load_dotenv()


def clean_url(url):
    """Normalize the company domain/URL by removing protocol, www., and trailing slashes."""
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip().lower()
    
    # Remove http:// or https://
    if url.startswith('http://'):
        url = url[len('http://'):]
    elif url.startswith('https://'):
        url = url[len('https://'):]
        
    # Remove www.
    if url.startswith('www.'):
        url = url[len('www.'):]
        
    # Remove trailing slash or paths to get just the base domain
    url = url.split('/')[0]
    
    return url

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


# ── Known field names Bright Data uses for the company's own website ─────────
# Jobs dataset schema varies by platform/version, so we try every known
# top-level name in priority order before giving up.
_DOMAIN_FIELD_CANDIDATES = [
    "company_website",
    "company_url",
    "company_page_link",
    "company_site",
    "website",
    "company_domain",
    "employer_website",
    "company_link",
    "external_apply_link",   # Indeed sometimes routes this to the employer's ATS/site
]

# ── Known nested paths — e.g. record["company_info"]["website"] ──────────────
_DOMAIN_NESTED_PATHS = [
    ("company_info",    "website"),
    ("company_info",    "url"),
    ("company_info",    "domain"),
    ("company_details", "website"),
    ("company_details", "url"),
    ("employer",        "website"),
    ("employer",        "url"),
]

# ── Regex to pull a bare URL out of free-text (e.g. job description) ─────────
_URL_IN_TEXT_REGEX = re.compile(
    r'https?://[^\s"\'<>\)]+',
    re.IGNORECASE
)

# ── Domains that belong to the job platforms / social networks themselves,
# never the hiring company. A "company_url" field on LinkedIn job records
# is very often the LinkedIn *company page*, not the employer's real site —
# without this filter, clean_url() would happily save "linkedin.com" as the
# domain for almost every row.
_PLATFORM_DOMAIN_BLOCKLIST = {
    "linkedin.com", "indeed.com", "glassdoor.com", "facebook.com",
    "twitter.com", "x.com", "instagram.com", "ziprecruiter.com",
    "monster.com", "google.com", "bing.com",
}


def _looks_like_company_domain(domain: str) -> bool:
    """True if a cleaned domain string is non-empty and not a platform's own domain."""
    if not domain:
        return False
    return not any(
        domain == blocked or domain.endswith("." + blocked)
        for blocked in _PLATFORM_DOMAIN_BLOCKLIST
    )


def extract_company_domain(record, platform):
    """
    Extracts the hiring company's website/domain from a Bright Data job record.

    WHY THIS IS HARD:
    - Field names differ across schema versions and between LinkedIn/Indeed.
    - LinkedIn's "company_url" is frequently the LinkedIn *company page*
      (linkedin.com/company/...), not the employer's actual website, so a
      naive extraction silently mislabels every row's domain as "linkedin.com".

    Strategy (in order of priority), skipping any candidate that resolves
    to a platform's own domain rather than the company's:
    1. Known top-level field name variants
    2. Known nested object paths (e.g. company_info.website)
    3. First URL found in the job/company description text
    4. Return "" if nothing usable is found (kept blank, not "N/A", to
       match the existing company_domain column convention)
    """

    # ── Step 1: Top-level flat fields ────────────────────────────────────
    for field in _DOMAIN_FIELD_CANDIDATES:
        raw = record.get(field)
        if raw and isinstance(raw, str) and raw.strip():
            domain = clean_url(raw)
            if _looks_like_company_domain(domain):
                return domain

    # ── Step 2: Nested object paths ──────────────────────────────────────
    for parent_key, child_key in _DOMAIN_NESTED_PATHS:
        parent = record.get(parent_key)
        if isinstance(parent, dict):
            raw = parent.get(child_key)
            if raw and isinstance(raw, str) and raw.strip():
                domain = clean_url(raw)
                if _looks_like_company_domain(domain):
                    return domain

    # ── Step 3: Scan description/summary text for any embedded URL ────────
    # Some listings mention "Learn more at acme.com" inside the body text.
    description_fields = [
        "description", "description_text", "job_description",
        "summary", "job_summary", "overview", "about",
    ]
    for field in description_fields:
        text = record.get(field, "")
        if text and isinstance(text, str):
            for match in _URL_IN_TEXT_REGEX.findall(text):
                domain = clean_url(match)
                if _looks_like_company_domain(domain):
                    return domain

    return ""


def normalize_record(record, platform):
    """Standardize field names from Bright Data API responses."""

    # Log all fields from the first record per platform — helps debug missing fields
    debug_record_fields(record, platform)

    job_title    = record.get("title") or record.get("job_title", "")
    company_name = record.get("company") or record.get("company_name", "")
    job_location = record.get("location") or record.get("job_location", "")
    url          = record.get("url") or record.get("job_url", "")
    company_domain = extract_company_domain(record, platform)

    if platform == "linkedin":
        return {
            "job_title":      job_title,
            "company_name":   company_name,
            "company_domain": company_domain,
            "job_location":   job_location,   # kept internally for dedup only, dropped before CSV export
            "job_url":        url,
            "date_posted":    record.get("posted_at") or record.get("posted_date", ""),
            "platform":       "LinkedIn"
        }
    elif platform == "indeed":
        return {
            "job_title":      job_title,
            "company_name":   company_name,
            "company_domain": company_domain,
            "job_location":   job_location,   # kept internally for dedup only, dropped before CSV export
            "job_url":        url,
            "date_posted":    record.get("posted_at") or record.get("date_posted_parsed") or record.get("date_posted", ""),
            "platform":       "Indeed"
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
    #   Company Name, Company Domain, Job Title, Job Posting URL,
    #   Portal, Country, Tier Signal, Date
    df = df.rename(columns={
        "company_name":   "Company Name",
        "company_domain": "Company Domain",
        "job_title":      "Job Title",
        "job_url":        "Job Posting URL",
        "platform":       "Portal",
        "search_country": "Country",
        "search_title":   "Tier Signal",   # the job-title query that surfaced this lead
        "date_posted":    "Date",
    })
    df = df[[
        "Company Name", "Company Domain", "Job Title", "Job Posting URL",
        "Portal", "Country", "Tier Signal", "Date",
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

def save_to_mongodb(df):
    """Saves/upserts the clean DataFrame to MongoDB collection (lead_outreach_db.jobs)."""
    if df is None or df.empty:
        return
        
    try:
        from pymongo import MongoClient, UpdateOne
        mongodb_uri = os.getenv("MONGODB_URI", "").strip()
        db_name = os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "lead_outreach_db")

        if not mongodb_uri or any(p in mongodb_uri for p in ["<username>", "<password>", "<db_username>", "username:password"]):
            logger.warning("⚠️ MONGODB_URI is not set in backend/.env. Skipping MongoDB Atlas sync.")
            return
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[db_name]
        collection = db["jobs"]
        
        records = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        for _, row in df.iterrows():
            company = str(row.get("Company Name") or "").strip()
            job_title = str(row.get("Job Title") or "").strip()
            if not company or not job_title:
                continue
                
            date_val = str(row.get("Date") or "").strip() if pd.notna(row.get("Date")) else ""
            posting_url = str(row.get("Job Posting URL") or "") if pd.notna(row.get("Job Posting URL")) else ""
            tier_sig = str(row.get("Tier Signal") or "").strip() if pd.notna(row.get("Tier Signal")) else "Unknown"
            doc = {
                "company": company,
                "company_domain": str(row.get("Company Domain") or "") if pd.notna(row.get("Company Domain")) else "",
                "job_title": job_title,
                "company_url": posting_url,
                "job_url": posting_url,
                "portal": str(row.get("Portal") or "BrightData") if pd.notna(row.get("Portal")) else "BrightData",
                "country": str(row.get("Country") or "United States") if pd.notna(row.get("Country")) else "United States",
                "tier_signal": tier_sig if tier_sig else "Unknown",
                "scraped_date": date_val if date_val else now_iso,
                "raw_data": {k: str(v) for k, v in row.items() if pd.notna(v)}
            }
            records.append(doc)
            
        if records:
            operations = []
            for r in records:
                filter_query = {"job_url": r["job_url"]} if r.get("job_url") else {
                    "company": r["company"],
                    "job_title": r["job_title"],
                    "country": r["country"],
                    "portal": r["portal"]
                }
                operations.append(UpdateOne(filter_query, {"$set": r}, upsert=True))
            res = collection.bulk_write(operations)
            logger.info(f"💾 Synced {len(records)} leads to MongoDB Atlas ({db_name}.jobs). Upserted: {res.upserted_count}, Modified: {res.modified_count}")
    except Exception as e:
        logger.warning(f"⚠️ Could not sync leads to MongoDB Atlas: {e}")

if __name__ == "__main__":
    logger.info("Loading config...")
    raw_file = os.path.join(os.path.dirname(__file__), "output", "scraped_raw_results.csv")
    leads_file = os.path.join(os.path.dirname(__file__), "output", "leads.csv")

    if os.path.exists(raw_file) and os.path.getsize(raw_file) > 0:
        logger.info(f"📥 Reading input: {raw_file} ...")
        try:
            df_raw = pd.read_csv(raw_file)
            clean_df = clean_and_filter(df_raw.to_dict(orient="records"))
            save_to_csv(clean_df)
            save_to_mongodb(clean_df)
        except Exception as e:
            logger.error(f"❌ Error processing {raw_file}: {e}")
    elif os.path.exists(leads_file) and os.path.getsize(leads_file) > 0:
        logger.info(f"📥 Reading existing leads: {leads_file} ...")
        try:
            df_leads = pd.read_csv(leads_file)
            save_to_mongodb(df_leads)
            logger.info("✅ Successfully synced existing leads into MongoDB Atlas.")
        except Exception as e:
            logger.error(f"❌ Error syncing {leads_file}: {e}")
    else:
        logger.warning(f"⚠️ Input file not found or empty: {raw_file}")
        logger.warning("⚠️ No data to process. To trigger live scraping from Bright Data, please run: python main.py")