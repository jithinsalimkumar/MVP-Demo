import os
import sys
import uvicorn

if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8050))
    print(f"Starting Lead Outreach Backend on http://localhost:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

