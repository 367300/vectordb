"""Утилиты для шифрования и дешифрования токенов."""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_encryption_key(password: str) -> bytes:
    """Генерирует ключ шифрования из пароля.
    
    Args:
        password: Пароль для генерации ключа
        
    Returns:
        bytes: Ключ в формате Fernet
    """
    password_bytes = password.encode()
    salt = b'vectordb_salt_2024'  # Фиксированная соль для консистентности
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key


def encrypt_token(token: str, encryption_key: str) -> str:
    """Шифрует JWT токен.
    
    Args:
        token: JWT токен для шифрования
        encryption_key: Ключ шифрования
        
    Returns:
        str: Зашифрованный токен (base64)
    """
    key = generate_encryption_key(encryption_key)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str, encryption_key: str) -> str:
    """Дешифрует зашифрованный JWT токен.
    
    Args:
        encrypted_token: Зашифрованный токен
        encryption_key: Ключ шифрования
        
    Returns:
        str: Дешифрованный JWT токен
        
    Raises:
        ValueError: Если токен не может быть дешифрован
    """
    try:
        key = generate_encryption_key(encryption_key)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Не удалось дешифровать токен: {e}")

