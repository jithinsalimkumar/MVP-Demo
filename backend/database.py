import os
from dotenv import load_dotenv
import motor.motor_asyncio

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "lead_outreach_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "jobs")

# Global variables for DB connection
client = None
db = None
is_mongo_connected = False

# In-memory storage fallback if MongoDB Atlas is unavailable/offline
in_memory_jobs = []
in_memory_scrapes = []

async def init_db():
    global client, db, is_mongo_connected

    # Check if user is using default placeholder URI
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
                serverSelectionTimeoutMS=3000
            )
            await test_client.admin.command('ping')
            client = test_client
            db = client[DB_NAME]
            is_mongo_connected = True
            print(f"[DB OK] MongoDB connected successfully to {label} ({DB_NAME}.{COLLECTION_NAME})")
            await sync_output_to_mongodb()
            return
        except Exception:
            continue

    # If no MongoDB instance could be reached:
    is_mongo_connected = False
    print("[INFO] Running in Demo Mode using built-in In-Memory Database.")
    print("[TIP] To connect your real database, update MONGODB_URI in backend/.env with your MongoDB Atlas connection string.")

async def update_existing_job(collection, job_doc):
    """
    Updates or inserts an individual job document into MongoDB based on unique identifiers:
    Prefer job_url; fallback to company + job_title + portal + country.
    """
    from pymongo import UpdateOne
    
    job_url = str(job_doc.get("job_url") or job_doc.get("company_url") or "").strip()
    if job_url:
        filter_query = {"job_url": job_url}
    else:
        filter_query = {
            "company": str(job_doc.get("company") or "").strip(),
            "job_title": str(job_doc.get("job_title") or "").strip(),
            "country": str(job_doc.get("country") or "United States").strip(),
            "portal": str(job_doc.get("portal") or "BrightData").strip()
        }

    return UpdateOne(filter_query, {"$set": job_doc}, upsert=True)

async def sync_output_to_mongodb():
    """Syncs existing output/leads.csv file into MongoDB and logs detailed metrics."""
    if not is_mongo_connected or db is None:
        return
        
    try:
        import pandas as pd
        from datetime import datetime, timezone

        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(base_dir, "scraper", "discovery", "output", "leads.csv")
        if not os.path.exists(csv_path):
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            return

        jobs_col = db[COLLECTION_NAME]
        db_count_before = await jobs_col.count_documents({})
        if db_count_before >= len(df):
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
            operations = [await update_existing_job(jobs_col, r) for r in records]
            res = await jobs_col.bulk_write(operations)
            db_count_after = await jobs_col.count_documents({})
            
            inserted = res.upserted_count
            updated = res.modified_count
            skipped = len(records) - (inserted + updated)
            
            print("─" * 50)
            print("MongoDB connected successfully.")
            print(f"Number of jobs scraped: {len(df)}")
            print(f"Number of new jobs inserted: {inserted}")
            print(f"Number of existing jobs updated: {updated}")
            print(f"Number of duplicate jobs skipped: {skipped}")
            print(f"Total jobs currently stored: {db_count_after}")
            print("─" * 50)
    except Exception as e:
        print(f"[DB SYNC WARN] Could not auto-sync output to MongoDB: {e}")

sync_csv_output_to_mongodb = sync_output_to_mongodb

def get_db():
    return db

def get_jobs_collection():
    if is_mongo_connected and db is not None:
        return db[COLLECTION_NAME]
    return None
