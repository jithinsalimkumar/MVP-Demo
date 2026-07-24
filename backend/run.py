import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8050))
    print(f"Starting Lead Outreach MVP Backend on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
