"""
JWT Authentication Module
Handles token creation, verification, and password hashing
"""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

logger = structlog.get_logger()

# Configuration - load from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData:
    """Parsed token data"""
    def __init__(self, user_id: str, email: str = None, tier: str = "free", exp: datetime = None):
        self.user_id = user_id
        self.email = email
        self.tier = tier
        self.exp = exp


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a JWT access token
    
    Args:
        data: Payload data (must include 'sub' for user_id)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    logger.debug("access_token_created", user_id=data.get("sub"), expires=expire.isoformat())
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    Generate a refresh token for token renewal
    
    Args:
        user_id: User identifier
        
    Returns:
        Encoded refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    logger.debug("refresh_token_created", user_id=user_id, expires=expire.isoformat())
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        TokenData with parsed claims
        
    Raises:
        HTTPException if token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        # Check token type
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type: expected {token_type}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token has expired")
        
        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            tier=payload.get("tier", "free"),
            exp=datetime.fromtimestamp(exp) if exp else None
        )
        
    except JWTError as e:
        logger.warning("token_verification_failed", error=str(e))
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return verify_token(credentials.credentials, token_type="access")


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[TokenData]:
    """
    Optional authentication - returns None if not authenticated
    """
    if credentials is None:
        return None
    
    try:
        return verify_token(credentials.credentials, token_type="access")
    except HTTPException:
        return None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("password_verification_error", error=str(e))
        return False


def generate_api_key(user_id: str, prefix: str = "zc_live_") -> str:
    """
    Generate an API key for a user
    
    Args:
        user_id: User identifier
        prefix: Key prefix (e.g., 'zc_live_' or 'zc_test_')
        
    Returns:
        API key string
    """
    import secrets
    import hashlib
    
    # Generate random component
    random_part = secrets.token_hex(16)
    
    # Create key
    api_key = f"{prefix}{random_part}"
    
    logger.info("api_key_generated", user_id=user_id, prefix=prefix)
    return api_key


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage
    We store hashed keys, not plain text
    """
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against its stored hash
    """
    return hash_api_key(provided_key) == stored_hash
