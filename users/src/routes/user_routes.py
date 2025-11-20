import logging

from fastapi import APIRouter, Depends, FastAPI

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from src.dependencies.auth import UserToken, VerifyToken, sign_jwt
from src.models import User
from src.models import Follow

import jwt

from src.dependencies.config import Config

from src.schemas import CreateUserRequest, LoginUserRequest

from src.dependencies.db import db_session as DB

config = Config()

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/hello")
async def hello(user: UserToken = Depends(VerifyToken)):
    return {"message": f"Hello, {user.username}"}


@router.post("/users/register")
async def register(req: CreateUserRequest):
    user = User(req.email, req.password, req.username)

    try:
        DB.add(user)
        DB.commit()
    except Exception as e:
        DB.rollback()
        return ({"message": "internal server error", "error": str(e)}), 500

    try:
        token = sign_jwt(str(user.id), str(user.username))
        return ({"user": user.to_dict(), "token": token}), 200
    except Exception as e:
        return ({"message": "internal server error", "error": str(e)}), 500


@router.post("/users/login")
async def login(req: LoginUserRequest):
    user: User = User.query.filter_by(email=req.email).first()

    if not user:
        return ({"message": "Invalid Login"}), 400

    if not user.verify_password(req.password):
        return ({"message": "Incorrect Password"}), 400

    try:
        token = jwt.encode(
            {"userId": str(user.id)}, config["JWT_SECRET"], algorithm="HS256"
        )
        return ({"user": user.to_dict(), "token": token}), 200
    except Exception as e:
        return ({"message": "internal server error", "error": str(e)}), 500
