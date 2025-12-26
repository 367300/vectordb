"""Утилита для генерации JWT токенов."""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt

# Загружаем переменные из .env файла
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()

def generate_token(expires_days: int = 30) -> str:
    """Генерирует JWT токен.
    
    Args:
        expires_days: Количество дней до истечения токена
        
    Returns:
        str: JWT токен
    """
    payload = {
        "sub": "test",
        "admin": True,
        "exp": datetime.utcnow() + timedelta(days=expires_days),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

if __name__ == "__main__":
    token = generate_token()
    print(f"JWT Token: {token}")
    print(f"\nИспользование:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/libraries/')

