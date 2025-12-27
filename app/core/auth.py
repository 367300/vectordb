"""JWT authentication utilities."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
from app.core.encryption import decrypt_token

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify encrypted JWT token from Authorization header.
    
    Сначала дешифрует токен, затем проверяет JWT подпись для защиты от подмены payload.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid, cannot be decrypted, or missing
    """
    try:
        # Дешифруем зашифрованный токен
        jwt_token = decrypt_token(credentials.credentials, settings.encryption_key)
        
        # Проверяем JWT подпись для защиты от подмены payload
        payload = jwt.decode(
            jwt_token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        return payload
    except ValueError as e:
        # Ошибка дешифрования
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token: decryption failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        # Ошибка проверки JWT подписи
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token: signature verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

