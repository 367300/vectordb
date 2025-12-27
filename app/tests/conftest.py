"""Pytest configuration and fixtures for tests."""

import os
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv
from jose import jwt

from app.core.encryption import encrypt_token

# Загружаем переменные из .env файла
load_dotenv()


@pytest.fixture
def jwt_token() -> str:
    """Генерирует зашифрованный JWT токен для тестов.
    
    Returns:
        str: Зашифрованный JWT токен
    """
    secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    encryption_key = os.getenv("ENCRYPTION_KEY", secret_key)
    payload = {
        "sub": "test",
        "admin": True,
        "exp": datetime.utcnow() + timedelta(days=1),
    }
    jwt_token = jwt.encode(payload, secret_key, algorithm="HS256")
    return encrypt_token(jwt_token, encryption_key)


@pytest.fixture
def auth_headers(jwt_token: str) -> dict:
    """Возвращает заголовки с JWT токеном для авторизации.
    
    Args:
        jwt_token: JWT токен из фикстуры
        
    Returns:
        dict: Заголовки с Authorization
    """
    return {"Authorization": f"Bearer {jwt_token}"}

