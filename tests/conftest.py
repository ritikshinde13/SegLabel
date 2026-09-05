import pytest
import os
import tempfile
from app import create_app
from config import Config
from database.db import init_db
from services.identity_manager import IdentityManager
from services.policy_engine import PolicyEngine
from services.communication_engine import CommunicationEngine
from services.audit_service import AuditService
from services.verification_service import VerificationService
from services.demo_service import DemoService

class TestConfig(Config):
    TESTING = True
    DEBUG = False

@pytest.fixture
def temp_db():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path, seed_defaults=True)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def app(temp_db):
    class AppTestConfig(TestConfig):
        DATABASE_PATH = temp_db

    flask_app = create_app(AppTestConfig)
    return flask_app

@pytest.fixture
def unauth_client(app):
    return app.test_client()

@pytest.fixture
def client(app):
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
    return test_client

@pytest.fixture
def services(temp_db):
    return {
        "identity": IdentityManager(temp_db),
        "policy": PolicyEngine(temp_db),
        "comm": CommunicationEngine(temp_db),
        "audit": AuditService(temp_db),
        "verification": VerificationService(temp_db),
        "demo": DemoService(temp_db),
        "db_path": temp_db
    }
