from dataclasses import dataclass
from fastapi import HTTPException, Request, Depends

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm.base import state_attribute_str

from src.dependencies.config import Config
from src.models import User

from typing import Dict


import jwt

config = Config()

JWT_SECRET = config["JWT_SECRET"]
JWT_ALGO = config["JWT_ALGO"]

security = HTTPBearer()


@dataclass
class UserToken:
    id: str
    username: str


def sign_jwt(user_id: str, username: str) -> str:
    token = jwt.encode(
        {"user_id": str(user_id), "username": username},
        config["JWT_SECRET"],
        algorithm="HS256",
    )
    return token


def decode_jwt(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, config["JWT_SECRET"], config["JWT_ALGO"])
        return decoded_token
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
