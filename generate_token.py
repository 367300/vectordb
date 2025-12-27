"""Утилита для генерации и шифрования JWT токенов."""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt

from app.core.encryption import encrypt_token

# Загружаем переменные из .env файла
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") or os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()

def generate_token(expires_days: int = 30, encrypt: bool = True, payload: dict = None) -> str:
    """Генерирует JWT токен и опционально шифрует его.
    
    Args:
        expires_days: Количество дней до истечения токена
        encrypt: Если True, токен будет зашифрован перед возвратом
        
    Returns:
        str: JWT токен (зашифрованный, если encrypt=True)
    """
    if payload is None:
        raise ValueError("Payload is required")
    return encrypt_token(jwt.encode(payload, SECRET_KEY, algorithm="HS256"), ENCRYPTION_KEY)

if __name__ == "__main__":
    print(f"Введите имя пользователя: ")
    sub = input()
    print(f"Пользователь администратор? (y/n): ")
    admin = input()
    if admin == "y":
        admin = True
    elif admin == "n":
        admin = False
    else:
        print("Неверный ввод!")
        exit(1)
    print("Дата истечения токена (в формате YYYY-MM-DD): ")
    exp = input()
    exp = datetime.strptime(exp, "%Y-%m-%d")
    payload = {
        "sub": sub,
        "admin": admin,
        "exp": exp,
    }
    
    try:
        encrypted_token = generate_token(encrypt=True, payload=payload)
        print(f"Зашифрованный JWT Token: {encrypted_token}")
    except ValueError as e:
        print(f"Ошибка: {e}")
        exit(1)
    print(f"\nИспользование:")
    print(f'curl -H "Authorization: Bearer {encrypted_token}" http://localhost:8000/libraries/')
