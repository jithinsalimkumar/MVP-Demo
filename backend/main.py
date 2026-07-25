from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

import database
from routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: Initialize MongoDB database connection
    await database.init_db()
    yield
    # Shutdown logic if needed

app = FastAPI(
    title="Lead Outreach System MVP API",
    description="Clean, lightweight FastAPI backend for Lead Outreach System MVP",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend (local dev & production Vercel deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3050",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3050",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api prefix and root
app.include_router(api_router, prefix="/api")
app.include_router(api_router)  # Also expose without prefix for max convenience

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Lead Outreach System MVP API",
        "mongo_connected": database.is_mongo_connected
    }

if __name__ == "__main__":
    import sys
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8050))
    print(f"Starting Lead Outreach Backend on http://localhost:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

