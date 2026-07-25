import os
from dotenv import load_dotenv
import motor.motor_asyncio

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "lead_outreach_db")
COLLECTION_NAME = "jobs"

# Global variables for DB connection
client = None
db = None
is_mongo_connected = False

# In-memory storage fallback if Atlas URI is unconfigured
in_memory_jobs = []
in_memory_scrapes = []

async def init_db():
    global client, db, is_mongo_connected

    atlas_uri = os.getenv("MONGODB_URI", "").strip()
    db_name = os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "lead_outreach_db")

    # Check if MONGODB_URI is provided and valid (not a template placeholder)
    is_valid_uri = bool(atlas_uri) and not any(p in atlas_uri for p in ["<username>", "<password>", "<db_username>", "username:password"])

    if not is_valid_uri:
        is_mongo_connected = False
        load_csv_to_in_memory()
        print("--------------------------------------------------")
        print("[WARNING] MONGODB_URI is not set in backend/.env")
        print("   Please set your MongoDB Atlas connection string in backend/.env")
        print("   Example: MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")
        print(f"   Database: {db_name} | Collection: {COLLECTION_NAME}")
        print("--------------------------------------------------")
        return

    try:
        test_client = motor.motor_asyncio.AsyncIOMotorClient(
            atlas_uri,
            serverSelectionTimeoutMS=5000
        )
        await test_client.admin.command('ping')
        client = test_client
        db = client[db_name]
        is_mongo_connected = True

        await db["jobs"].create_index("job_url", background=True)

        print("--------------------------------------------------")
        print("Connected to MongoDB Atlas")
        print(f"Database: {db_name}")
        print(f"Collection: {COLLECTION_NAME}")
        print("--------------------------------------------------")

        await sync_csv_output_to_mongodb()
    except Exception as err:
        is_mongo_connected = False
        load_csv_to_in_memory()
        print("--------------------------------------------------")
        print("[ERROR] Failed to connect to MongoDB Atlas at configured MONGODB_URI:")
        print(f"   Error: {err}")
        print("   Please check network connectivity, IP whitelist, and credentials in backend/.env")
        print("--------------------------------------------------")



def load_csv_to_in_memory():
    global in_memory_jobs
    if in_memory_jobs:
        return
    try:
        import pandas as pd
        from datetime import datetime, timezone
        from bson import ObjectId

        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(base_dir, "scraper", "discovery", "output", "leads.csv")
        if not os.path.exists(csv_path):
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        records = []
        for idx, row in df.iterrows():
            company = str(row.get("Company Name") or "").strip()
            job_title = str(row.get("Job Title") or "").strip()
            if not company or not job_title:
                continue

            date_val = str(row.get("Date") or "").strip() if pd.notna(row.get("Date")) else ""
            posting_url = str(row.get("Job Posting URL") or "") if pd.notna(row.get("Job Posting URL")) else ""
            tier_sig = str(row.get("Tier Signal") or "").strip() if pd.notna(row.get("Tier Signal")) else "Unknown"
            doc = {
                "id": str(ObjectId()),
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
        in_memory_jobs = records
    except Exception as e:
        print(f"[WARN] Could not load leads.csv into in-memory fallback: {e}")


async def sync_csv_output_to_mongodb():
    """Syncs existing output/leads.csv file into MongoDB via upsert matching on job_url."""
    if not is_mongo_connected or db is None:
        return
        
    try:
        import pandas as pd
        from datetime import datetime, timezone
        from pymongo import UpdateOne

        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(base_dir, "scraper", "discovery", "output", "leads.csv")
        if not os.path.exists(csv_path):
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        jobs_col = db["jobs"]

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
            await jobs_col.bulk_write(operations)
            print(f"[DB SYNC] Automatically synced {len(records)} scraped leads from leads.csv into MongoDB Atlas ({DB_NAME}.jobs)")
    except Exception as e:
        print(f"[DB SYNC WARN] Could not auto-sync leads.csv into MongoDB: {e}")

def get_db():
    return db

def get_jobs_collection():
    if is_mongo_connected and db is not None:
        return db["jobs"]
    return None
