"""Pytest configuration and fixtures for tests."""

import os
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv
from jose import jwt

# Загружаем переменные из .env файла
load_dotenv()


@pytest.fixture
def jwt_token() -> str:
    """Генерирует JWT токен для тестов.
    
    Returns:
        str: JWT токен
    """
    secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    payload = {
        "sub": "test",
        "admin": True,
        "exp": datetime.utcnow() + timedelta(days=1),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


@pytest.fixture
def auth_headers(jwt_token: str) -> dict:
    """Возвращает заголовки с JWT токеном для авторизации.
    
    Args:
        jwt_token: JWT токен из фикстуры
        
    Returns:
        dict: Заголовки с Authorization
    """
    return {"Authorization": f"Bearer {jwt_token}"}

