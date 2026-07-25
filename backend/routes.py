import os
import sys
import importlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from bson import ObjectId

from models import LoginRequest, LoginResponse, ScrapeRequest, JobDocument, DashboardStats
import database

router = APIRouter()

# -----------------------------------------------------------------------------
# DYNAMIC SCRAPER LOADER FROM backend/scraper/ FOLDER
# -----------------------------------------------------------------------------
def get_custom_scraper_runner():
    """
    Checks if a custom scraping function exists inside backend/scraper/ or backend/scraper/discovery/.
    Adapts functions like run_module1() or scrape_all() to return standardized job records.
    """
    try:
        base_dir = os.path.dirname(__file__)
        discovery_dir = os.path.join(base_dir, "scraper", "discovery")
        scraper_dir = os.path.join(base_dir, "scraper")
        
        for d in [discovery_dir, scraper_dir]:
            if os.path.exists(d) and d not in sys.path:
                sys.path.insert(0, d)

        mod = None
        for mod_name in ["main", "bright_data", "processor"]:
            try:
                mod = importlib.import_module(mod_name)
                if hasattr(mod, "run_scrape") or hasattr(mod, "scrape") or hasattr(mod, "scrape_all") or hasattr(mod, "run_module1"):
                    break
            except Exception:
                continue

        if not mod:
            return None

        def runner_adapter(country: str, job_keyword: str, limit: int = 10) -> List[dict]:
            token = os.getenv("BRIGHT_DATA_TOKEN")
            if not token and (hasattr(mod, "scrape_all") or hasattr(mod, "run_module1")):
                # Check token if scraper relies on Bright Data API
                raise ValueError("BRIGHT_DATA_TOKEN is not set in backend/.env file. Please add your Bright Data API token.")

            raw_records = []
            if hasattr(mod, "run_scrape"):
                raw_records = mod.run_scrape(country=country, job_keyword=job_keyword, limit=limit)
            elif hasattr(mod, "scrape"):
                raw_records = mod.scrape(country=country, job_keyword=job_keyword, limit=limit)
            elif hasattr(mod, "scrape_all"):
                generator = mod.scrape_all([job_keyword], [country])
                for chunk in generator:
                    if chunk:
                        raw_records.extend(chunk)
                        if len(raw_records) >= limit:
                            break
            elif hasattr(mod, "run_module1"):
                df = mod.run_module1()
                if df is not None and hasattr(df, "to_dict"):
                    raw_records = df.to_dict(orient="records")

            formatted_records = []
            now_iso = datetime.now(timezone.utc).isoformat()

            for item in (raw_records or [])[:limit]:
                if isinstance(item, dict):
                    formatted_records.append({
                        "_id": str(ObjectId()),
                        "company": str(item.get("Company Name") or item.get("company") or "Unknown Company"),
                        "job_title": str(item.get("Job Title") or item.get("job_title") or job_keyword),
                        "country": str(item.get("Country") or item.get("country") or country),
                        "portal": str(item.get("Portal") or item.get("source_platform") or item.get("portal") or "BrightData"),
                        "company_url": str(item.get("Company Domain") or item.get("Job Posting URL") or item.get("company_url") or ""),
                        "job_url": str(item.get("Job Posting URL") or item.get("job_url") or item.get("company_url") or ""),
                        "tier_signal": str(item.get("Tier Signal") or item.get("tier_signal") or item.get("search_title") or "Unknown"),
                        "scraped_date": str(item.get("Date") or item.get("scraped_date") or now_iso),
                        "raw_data": {k: str(v) for k, v in item.items() if k != "_id"}
                    })

            return formatted_records

        return runner_adapter
    except Exception:
        pass
    return None



# -----------------------------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Simple demo login endpoint comparing credentials with .env file settings."""
    env_user = os.getenv("ADMIN_USERNAME", "admin")
    env_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if credentials.username == env_user and credentials.password == env_pass:
        return LoginResponse(
            success=True,
            message="Login successful",
            token="demo-session-token-lead-outreach-2026",
            username=credentials.username
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@router.post("/scrape")
async def trigger_scrape(req: ScrapeRequest):
    """
    Executes scraping logic from backend/scraper/ folder if present and saves scraped job records to MongoDB.
    """
    scraper_fn = get_custom_scraper_runner()

    if not scraper_fn:
        return {
            "success": True,
            "message": "Scraper directory 'backend/scraper/' is ready. Please add your Bright Data scraping files inside backend/scraper/ to run live scraping.",
            "count": 0,
            "activity": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "country": req.country,
                "job_keyword": req.job_keyword,
                "count": 0
            }
        }

    # Execute custom scraping logic from backend/scraper/
    try:
        new_records = scraper_fn(
            country=req.country,
            job_keyword=req.job_keyword,
            limit=req.limit
        ) or []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing custom scraper in backend/scraper/: {str(e)}"
        )

    jobs_collection = database.get_jobs_collection()
    inserted_count = 0

    if new_records:
        if database.is_mongo_connected and jobs_collection is not None:
            from pymongo import UpdateOne
            operations = []
            for r in new_records:
                # Remove _id if set to auto-generated string so MongoDB handles _id on insert
                r_copy = dict(r)
                r_copy.pop("_id", None)
                r_copy.pop("id", None)
                filter_query = {"job_url": r_copy["job_url"]} if r_copy.get("job_url") else {
                    "company": r_copy.get("company"),
                    "job_title": r_copy.get("job_title"),
                    "country": r_copy.get("country"),
                    "portal": r_copy.get("portal")
                }
                operations.append(UpdateOne(filter_query, {"$set": r_copy}, upsert=True))
            
            res = await jobs_collection.bulk_write(operations)
            inserted_count = res.upserted_count + res.modified_count
        else:
            for rec in new_records:
                if "_id" not in rec:
                    rec["_id"] = str(ObjectId())
                database.in_memory_jobs.append(rec)
            inserted_count = len(new_records)

    activity_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "country": req.country,
        "job_keyword": req.job_keyword,
        "count": inserted_count
    }
    database.in_memory_scrapes.append(activity_entry)

    return {
        "success": True,
        "message": f"Successfully processed scraper output and saved {inserted_count} jobs.",
        "count": inserted_count,
        "activity": activity_entry
    }

@router.get("/filters")
async def get_job_filters():
    """
    Get dynamic distinct filter options (countries, portals, tier_signals) stored in MongoDB.
    """
    jobs_collection = database.get_jobs_collection()
    
    if database.is_mongo_connected and jobs_collection is not None:
        countries = await jobs_collection.distinct("country")
        portals = await jobs_collection.distinct("portal")
        tier_signals = await jobs_collection.distinct("tier_signal")
    else:
        countries = list(set(j.get("country") for j in database.in_memory_jobs if j.get("country")))
        portals = list(set(j.get("portal") for j in database.in_memory_jobs if j.get("portal")))
        tier_signals = list(set(j.get("tier_signal") for j in database.in_memory_jobs if j.get("tier_signal")))

    return {
        "countries": sorted([str(c) for c in countries if c]),
        "portals": sorted([str(p) for p in portals if p]),
        "tier_signals": sorted([str(t) for t in tier_signals if t])
    }

@router.get("/jobs")
async def get_jobs(
    search: Optional[str] = Query(None, description="Search query across company or job title"),
    country: Optional[str] = Query(None, description="Filter by country"),
    portal: Optional[str] = Query(None, description="Filter by portal"),
    tier_signal: Optional[str] = Query(None, description="Filter by tier signal"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get paginated jobs with search and filter capabilities directly from MongoDB.
    """
    jobs_collection = database.get_jobs_collection()
    
    if database.is_mongo_connected and jobs_collection is not None:
        query = {}
        if search:
            query["$or"] = [
                {"company": {"$regex": search, "$options": "i"}},
                {"job_title": {"$regex": search, "$options": "i"}},
                {"portal": {"$regex": search, "$options": "i"}},
                {"tier_signal": {"$regex": search, "$options": "i"}}
            ]
        if country and country != "All":
            query["country"] = country
        if portal and portal != "All":
            query["portal"] = portal
        if tier_signal and tier_signal != "All":
            query["tier_signal"] = tier_signal

        total = await jobs_collection.count_documents(query)
        cursor = jobs_collection.find(query).sort("scraped_date", -1).skip((page - 1) * limit).limit(limit)
        
        items = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            if not doc.get("job_url"):
                doc["job_url"] = doc.get("company_url", "")
            if not doc.get("tier_signal"):
                doc["tier_signal"] = "Unknown"
            items.append(doc)
    else:
        filtered = list(database.in_memory_jobs)
        if search:
            s = search.lower()
            filtered = [
                j for j in filtered
                if s in j.get("company", "").lower() or s in j.get("job_title", "").lower() or s in j.get("portal", "").lower() or s in j.get("tier_signal", "").lower()
            ]
        if country and country != "All":
            filtered = [j for j in filtered if j.get("country") == country]
        if portal and portal != "All":
            filtered = [j for j in filtered if j.get("portal") == portal]
        if tier_signal and tier_signal != "All":
            filtered = [j for j in filtered if j.get("tier_signal") == tier_signal]
            
        filtered.sort(key=lambda x: x.get("scraped_date", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * limit
        items = filtered[start:start + limit]
        for item in items:
            if "_id" in item and "id" not in item:
                item["id"] = str(item["_id"])
            if not item.get("job_url"):
                item["job_url"] = item.get("company_url", "")
            if not item.get("tier_signal"):
                item["tier_signal"] = "Unknown"

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """Get single job record by ID."""
    jobs_collection = database.get_jobs_collection()

    if database.is_mongo_connected and jobs_collection is not None:
        try:
            doc = await jobs_collection.find_one({"_id": ObjectId(job_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return doc
        except Exception:
            pass

    for item in database.in_memory_jobs:
        if item.get("id") == job_id or str(item.get("_id")) == job_id:
            item["id"] = str(item.get("id") or item.get("_id"))
            return item

    raise HTTPException(status_code=404, detail="Job not found")

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get aggregated dashboard stats directly from MongoDB (Total Jobs, Total Companies, Last Scrape Time, Total Records).
    """
    jobs_collection = database.get_jobs_collection()

    if database.is_mongo_connected and jobs_collection is not None:
        total_jobs = await jobs_collection.count_documents({})
        companies_pipeline = [{"$group": {"_id": "$company"}}, {"$count": "total_companies"}]
        comp_res = await jobs_collection.aggregate(companies_pipeline).to_list(1)
        total_companies = comp_res[0]["total_companies"] if comp_res else 0

        latest_doc = await jobs_collection.find_one(sort=[("scraped_date", -1)])
        last_scrape_time = latest_doc["scraped_date"] if latest_doc else None

        recent_cursor = jobs_collection.find().sort("scraped_date", -1).limit(5)
        recent = []
        async for d in recent_cursor:
            recent.append({
                "company": d.get("company"),
                "job_title": d.get("job_title"),
                "country": d.get("country"),
                "portal": d.get("portal"),
                "scraped_date": d.get("scraped_date")
            })
    else:
        total_jobs = len(database.in_memory_jobs)
        companies = set(j.get("company", "") for j in database.in_memory_jobs if "company" in j)
        total_companies = len(companies)
        last_scrape_time = database.in_memory_jobs[0]["scraped_date"] if database.in_memory_jobs else None
        recent = database.in_memory_jobs[:5]

    return DashboardStats(
        total_jobs=total_jobs,
        total_companies=total_companies,
        last_scrape_time=last_scrape_time,
        total_records=total_jobs,
        recent_activity=recent
    )
