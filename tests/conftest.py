import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app import database, storage
from app.config import get_settings
from app.main import app

BUCKET = "test-bucket"


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", BUCKET)
    monkeypatch.setenv("CDN_BASE_URL", "https://cdn.example.com")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
def engine():
    # SQLite 記憶體資料庫；StaticPool 讓每次連線都拿到同一個資料庫
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  content VARCHAR(1000) NOT NULL,
                  image_key VARCHAR(255) NOT NULL,
                  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    return engine


@pytest.fixture
def s3(settings):
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture
def client(engine, s3):
    app.dependency_overrides[database.get_engine] = lambda: engine
    app.dependency_overrides[storage.get_s3_client] = lambda: s3
    yield TestClient(app)
    app.dependency_overrides.clear()
