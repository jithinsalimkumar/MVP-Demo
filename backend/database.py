import os
from dotenv import load_dotenv
import motor.motor_asyncio

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("DB_NAME", "lead_outreach_db")

# Global variables for DB connection
client = None
db = None
is_mongo_connected = False

# In-memory storage fallback if MongoDB Atlas is unavailable/offline
in_memory_jobs = []
in_memory_scrapes = []

async def init_db():
    global client, db, is_mongo_connected

    # Check if user is using the default placeholder URI
    is_placeholder = not MONGODB_URI or "demo:demo123@cluster0.mongodb.net" in MONGODB_URI

    connection_candidates = []
    if not is_placeholder:
        connection_candidates.append(("MongoDB Atlas / Custom URI", MONGODB_URI))
    
    # Add local MongoDB as fallback candidate
    connection_candidates.append(("Local MongoDB", "mongodb://127.0.0.1:27017"))

    for label, uri in connection_candidates:
        try:
            test_client = motor.motor_asyncio.AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=2000
            )
            await test_client.admin.command('ping')
            client = test_client
            db = client[DB_NAME]
            is_mongo_connected = True
            print(f"[DB OK] Connected successfully to {label} ({DB_NAME})")
            await sync_csv_output_to_mongodb()
            return
        except Exception:
            continue

    # If no MongoDB instance could be reached:
    is_mongo_connected = False
    print("[INFO] Running in Demo Mode using built-in In-Memory Database.")
    print("[TIP] To connect your real database, update MONGODB_URI in backend/.env with your MongoDB Atlas connection string.")

async def sync_csv_output_to_mongodb():
    """Syncs existing output/leads.csv file into MongoDB if collection has fewer records than CSV."""
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
        db_count = await jobs_col.count_documents({})
        if db_count >= len(df):
            return

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
            operations = [
                UpdateOne(
                    {
                        "company": r["company"],
                        "job_title": r["job_title"],
                        "country": r["country"],
                        "portal": r["portal"]
                    },
                    {"$set": r},
                    upsert=True
                )
                for r in records
            ]
            await jobs_col.bulk_write(operations)
            print(f"[DB SYNC] Automatically synced {len(records)} scraped leads from leads.csv into MongoDB ({DB_NAME}.jobs)")
    except Exception as e:
        print(f"[DB SYNC WARN] Could not auto-sync leads.csv into MongoDB: {e}")

def get_db():
    return db

def get_jobs_collection():
    if is_mongo_connected and db is not None:
        return db["jobs"]
    return None
