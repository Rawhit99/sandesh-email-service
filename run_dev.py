"""Run the FastAPI app from repository root (fixes: uvicorn main:app from wrong cwd).

Usage: python run_dev.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", "8000")),
        reload=True,
        reload_dirs=[BACKEND],
    )
