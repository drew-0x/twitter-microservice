import logging

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from src.dependencies.auth import VerifyToken
from src.models import User
from src.models import Follow

from src.dependencies.config import Config

from src.dependencies.db import db_session as DB
from src.schemas import CreateFollowerRequset

config = Config()

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/follow")
def CreateFollow(follow: CreateFollowerRequset, user=Depends(VerifyToken)):

    if follow.following_id == user.id:
        return ({"error": "can not follow self"}), 400

    follow = Follow(user.id, follow.following_id)

    userFollowing: User = User.query.filter_by(id=follow.following_id).first()

    if not userFollowing:
        raise HTTPException(status_code=403, detail="user not found")
    userFollowing.increment_followers()

    try:
        DB.add(follow)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        return ({"error": str(e)}), 500

    return ("User Followed"), 200


@router.get("/follow")
def GetUsersFollowers(user=Depends(VerifyToken)):
    followers = Follow.query.filter_by(following_id=user.id).all()

    if not followers:
        return {"eror": "could not find any followers"}
    return ({"result": [follower.to_dict() for follower in followers]}), 200


@router.get("/following")
def GetUsersFollowing(user=Depends(VerifyToken)):
    followers = Follow.query.filter_by(follower_id=user.id).all()

    if not followers:
        return {"eror": "could not find any followers"}
    return ({"result": [follower.to_dict() for follower in followers]}), 200


@router.get("/follow/<id>")
def GetFollowByID(id: str):
    if not id:
        return ({"eror": "invalid id"}), 401
    follow = DB.query(Follow).filter_by(id=id).first()
    if not follow:
        return ({"eror": "could not find follow"}), 404
    return ({"result": follow.to_dict()}), 200


@router.delete("/follow/<following_id>")
def DeleteFollow(following_id: str, user: User = Depends(VerifyToken)):
    follow = DB.query(Follow).filter(
        and_(Follow.follower_id == user.id, Follow.following_id == following_id)  # type: ignore
    )

    try:
        DB.delete(follow)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        return ({"error": str(e)}), 500

    return (), 204
