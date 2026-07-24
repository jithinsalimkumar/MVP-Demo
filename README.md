# LeadPulse Enterprise Platform

LeadPulse is an enterprise lead intelligence platform built with **Next.js (App Router)** on the frontend and **FastAPI** on the backend, integrated with **Bright Data** scrapers and **MongoDB** for real-time lead discovery and job tracking.

Repository: [https://github.com/jithinsalimkumar/MVP-Demo](https://github.com/jithinsalimkumar/MVP-Demo)

---

## Quick Start Guide

### 1. Start the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the backend (choose either command):
   ```bash
   python main.py
   ```
   *or*
   ```bash
   python run.py
   ```

   The backend will start at **http://localhost:8050** (Host: `0.0.0.0`, Port: `8050`, Reload: `Enabled`).
   Interactive API Documentation (Swagger) is available at **http://localhost:8050/docs**.

---

### 2. Start the Frontend

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

   The frontend will start at **http://localhost:3050**.

---

## Demo Credentials

Sign in at **http://localhost:3050/login** using:
- **Username**: `admin`
- **Password**: `admin123`

*(Configurable via `backend/.env`)*

---

## Bright Data Scraper Integration

Place your Bright Data scraping files inside the empty directory:
```text
backend/
└── scraper/
```

Expose a entrypoint function in your scraper module such as `run_scrape(country, job_keyword, limit) -> List[dict]`.
The backend API (`POST /api/scrape`) automatically detects and executes your scraping code and saves the resulting records into MongoDB Atlas without requiring changes to any other application code.

---

## Project Directory Structure

```text
MVP/
├── README.md                 <-- Project documentation
├── backend/
│   ├── .env                  <-- Port & DB configuration (PORT=8050)
│   ├── database.py           <-- MongoDB Atlas connection & fallback
│   ├── main.py               <-- FastAPI app & entrypoint (python main.py)
│   ├── models.py             <-- Pydantic schemas
│   ├── requirements.txt      <-- Python dependencies
│   ├── routes.py             <-- REST API routes (/login, /scrape, /jobs, /dashboard)
│   ├── run.py                <-- Alternate start script (python run.py)
│   └── scraper/              <-- Empty folder for custom Bright Data scraper
└── frontend/
    ├── .env.local            <-- NEXT_PUBLIC_API_URL=http://localhost:8050/api
    ├── package.json          <-- Frontend scripts (dev & start on port 3050)
    ├── next.config.mjs       <-- API proxy rewrite rules
    └── src/
        ├── app/              <-- Next.js App Router pages (login, dashboard, scrape, jobs)
        ├── components/       <-- Modern UI components
        ├── context/          <-- Auth context
        └── lib/              <-- API client fetcher
```
