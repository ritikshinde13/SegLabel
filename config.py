import os
import secrets
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Use environment secret key or generate a cryptographic 256-bit token
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE_PATH = os.environ.get("SEGLABEL_DB", str(BASE_DIR / "seglabel.db"))
    
    # Session Cookie Security (OWASP ASVS Standard)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0").lower() in ("1", "true")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    
    # DoS & Payload Upload Mitigation (Max 16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    TESTING = False
    DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")

class TestConfig(Config):
    DATABASE_PATH = ":memory:"
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-deterministic-signing-key-seglabel"
