import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app
from app.database import get_db, Base
from app.models import User
from app.core.security import get_password_hash, create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_package_json():
    """Sample package.json content for testing."""
    return {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "4.17.1",
            "lodash": "4.17.19",
            "axios": "0.21.0"
        },
        "devDependencies": {
            "eslint": "7.32.0",
            "jest": "27.0.6"
        }
    }


@pytest.fixture
def sample_requirements_txt():
    """Sample requirements.txt content for testing."""
    return """requests==2.28.0
flask>=2.0.0
django==3.2.0
numpy==1.21.0
pytest==7.1.0"""