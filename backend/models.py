from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    username: Optional[str] = None

class ScrapeRequest(BaseModel):
    country: str = Field(default="United States", description="Country to scrape jobs for")
    job_keyword: str = Field(default="Software Engineer", description="Keyword or title to search")
    limit: int = Field(default=10, ge=1, le=100, description="Number of job records to return")

class JobDocument(BaseModel):
    id: Optional[str] = None
    company: str
    job_title: str
    country: str
    portal: str
    company_url: Optional[str] = ""
    job_url: Optional[str] = ""
    tier_signal: Optional[str] = ""
    scraped_date: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class DashboardStats(BaseModel):
    total_jobs: int
    total_companies: int
    last_scrape_time: Optional[str] = None
    total_records: int
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
