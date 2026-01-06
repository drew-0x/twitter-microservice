from dataclasses import dataclass
from fastapi import HTTPException, Depends

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.dependencies.config import Config

from typing import Dict

import os
import logging
import jwt

logger = logging.getLogger(__name__)
config = Config()

# JWT configuration - prefer environment variable, fall back to config for dev
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = config.get("JWT_SECRET")
    if JWT_SECRET:
        logger.warning(
            "JWT_SECRET loaded from .env file. "
            "For production, set JWT_SECRET as an environment variable."
        )
    else:
        raise ValueError(
            "JWT_SECRET must be set. Add to .env file or set as environment variable."
        )

JWT_ALGO = os.getenv("JWT_ALGO") or config.get("JWT_ALGO", "HS256")

security = HTTPBearer()


@dataclass
class UserToken:
    id: str
    username: str


def decode_jwt(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")
    except Exception as e:
        return {}


async def VerifyToken(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = decode_jwt(token)

        user_id: str = payload["user_id"]
        username: str = payload["username"]

        decoded_token = UserToken(user_id, username)

        return decoded_token

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Expired JWT Token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid JWT Token")
