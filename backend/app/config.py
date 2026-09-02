import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DB_PATH = BACKEND_DIR / "trustlens.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

# Score below this on any dimension flags an item for review.
FLAG_THRESHOLD = int(os.environ.get("FLAG_THRESHOLD", "70"))

# Color-coding thresholds for the run overview dashboard.
SCORE_GREEN_THRESHOLD = int(os.environ.get("SCORE_GREEN_THRESHOLD", "80"))
SCORE_YELLOW_THRESHOLD = int(os.environ.get("SCORE_YELLOW_THRESHOLD", "60"))

MAX_JUDGE_RETRIES = int(os.environ.get("MAX_JUDGE_RETRIES", "3"))
JUDGE_CONCURRENCY = int(os.environ.get("JUDGE_CONCURRENCY", "5"))

_default_origins = "http://localhost:5173,http://localhost:3000"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
