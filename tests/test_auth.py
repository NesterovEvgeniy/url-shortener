import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database and tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_register_duplicate_user():
    # Первый раз регистрируем пользователя
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "testpassword"}
    )
    
    # Попытка повторной регистрации
    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "testpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success():
    # Регистрируем пользователя
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "testpassword"}
    )
    
    # Вход
    response = client.post(
        "/auth/token",
        data={"username": "login@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/auth/token",
        data={"username": "nonexistent@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_optional_authentication():
    """Тест для необязательной аутентификации"""
    # Тест доступа без токена авторизации (должен создать ссылку для анонимного пользователя)
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/anonymous"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["owner_id"] is None  # Должен быть null, так как пользователь анонимный