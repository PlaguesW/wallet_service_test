import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app
from app.database import get_db, Base
from app.redis_client import redis_client

# Test database URL
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/wallet_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis database before and after each test."""
    try:
        redis_client.redis.flushdb()
    except:
        pass
    yield
    try:
        redis_client.redis.flushdb()
    except:
        pass

@pytest.fixture
def wallet_uuid():
    return "550e8400-e29b-41d4-a716-446655440000"