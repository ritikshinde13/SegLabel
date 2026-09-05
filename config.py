import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "seglabel-dev-secret-key-2026")
    DATABASE_PATH = os.environ.get("SEGLABEL_DB", str(BASE_DIR / "seglabel.db"))
    TESTING = False
    DEBUG = True

class TestConfig(Config):
    DATABASE_PATH = ":memory:"
    TESTING = True
    DEBUG = False
