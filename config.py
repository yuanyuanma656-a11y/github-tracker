import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "data" / "github_tracker.db"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "github_tracker.log"

REPORT_DIR = BASE_DIR / "reports"

GITHUB_API_URL = "https://api.github.com"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")