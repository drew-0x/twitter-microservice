import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from src.dependencies.auth import VerifyToken, UserToken
from src.dependencies.db import get_db
from src.models import User, Follow
from src.schemas import CreateFollowerRequset

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/follow")
def CreateFollow(
    follow: CreateFollowerRequset,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    if follow.following_id == user.id:
        raise HTTPException(status_code=400, detail="can not follow self")

    new_follow = Follow(user.id, follow.following_id)

    userFollowing: User = db.query(User).filter_by(id=new_follow.following_id).first()

    if not userFollowing:
        raise HTTPException(status_code=404, detail="user not found")
    userFollowing.increment_followers()

    try:
        db.add(new_follow)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating follow: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "User Followed"}


@router.get("/follow")
def GetUsersFollowers(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    followers = db.query(Follow).filter_by(following_id=user.id).all()

    if not followers:
        return {"result": []}
    return {"result": [follower.to_dict() for follower in followers]}


@router.get("/following")
def GetUsersFollowing(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    following = db.query(Follow).filter_by(follower_id=user.id).all()

    if not following:
        return {"result": []}
    return {"result": [f.to_dict() for f in following]}


@router.get("/follow/{id}")
def GetFollowByID(
    id: str,
    db: Session = Depends(get_db),
):
    if not id:
        raise HTTPException(status_code=400, detail="invalid id")
    follow = db.query(Follow).filter_by(id=id).first()
    if not follow:
        raise HTTPException(status_code=404, detail="could not find follow")
    return {"result": follow.to_dict()}


@router.delete("/follow/{following_id}")
def DeleteFollow(
    following_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    follow = db.query(Follow).filter(
        and_(Follow.follower_id == user.id, Follow.following_id == following_id)  # type: ignore
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="follow not found")

    try:
        db.delete(follow)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting follow: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return Response(status_code=204)
