import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.dependencies.mq import produce_message
from src.dependencies.db import get_db
from src.dependencies.auth import UserToken, VerifyToken
from src.models import Tweet, TweetRepost, ReplyTweet, TweetLike
from src.grpc.client import IncrementTweets
from src.schemas import CreateReplyRequest, CreateTweetRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    """Health check endpoint for load balancers and k8s probes."""
    return {"status": "healthy", "service": "tweets-service"}


@router.post("/tweet")
def createTweet(
    req: CreateTweetRequest,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet = Tweet(user.id, req.content)

    try:
        db.add(tweet)
        db.commit()
        db.refresh(tweet)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating tweet: {e}")
        raise HTTPException(status_code=500, detail="database error")

    IncrementTweets(user.id)

    produce_message(tweet.to_dict(), "general_tweets")  # Produce to tweet feed queue

    produce_message(  # Produce to the tweet event queue
        tweet.to_dict(), "tweet_events", "tweet.create"
    )
    return {"message": "tweet created"}


@router.get("/tweet")
def getTweets(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweets = db.query(Tweet).filter_by(user_id=user.id).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="Invalid Request")

    res = [tweet.to_dict() for tweet in tweets]

    return {"result": res}


@router.get("/tweet/{tweet_id}")
def getTweetByID(
    tweet_id: str,
    db: Session = Depends(get_db),
):
    tweet = db.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    replyTweets = db.query(ReplyTweet).filter_by(parent_id=tweet.id).all()

    replyTweetsRes = [t.to_dict() for t in replyTweets]

    return {"tweet": tweet.to_dict(), "replys": replyTweetsRes}


@router.delete("/tweet/{tweet_id}")
def deleteTweet(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet = db.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(tweet.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthorized")

    try:
        db.delete(tweet)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting tweet: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "tweet deleted"}


@router.post("/tweet/reply")
def createTweetReply(
    req: CreateReplyRequest,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet = ReplyTweet(user.id, req.parent_id, req.content)

    try:
        db.add(tweet)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating reply: {e}")
        raise HTTPException(status_code=500, detail="database error")

    IncrementTweets(user.id)
    return {"message": "tweet created"}


@router.get("/tweet/reply")
def getTweetReplys(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweets = db.query(ReplyTweet).filter_by(user_id=user.id).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [tweet.to_dict() for tweet in tweets]

    return {"result": res}


@router.delete("/tweet/reply/{tweet_id}")
def deleteTweetReply(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet = db.query(ReplyTweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(tweet.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthorized")

    try:
        db.delete(tweet)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting reply: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "tweet deleted"}


@router.post("/tweet/like/{tweet_id}")
def createLike(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet: Tweet = db.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    like = TweetLike(user.id, tweet_id)
    tweet.increment_likes()

    try:
        db.add(like)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating like: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "like created"}


@router.get("/tweet/like")
def getLikes(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    likes = db.query(TweetLike).filter_by(user_id=user.id).all()

    if not likes:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [like.to_dict() for like in likes]

    return {"result": res}


@router.delete("/tweet/like/{tweet_id}")
def deleteLike(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    like = db.query(TweetLike).filter_by(id=tweet_id).first()

    if not like:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(like.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthorized")

    tweet = db.query(Tweet).filter_by(id=like.tweet_id).first()
    if tweet:
        tweet.decrement_likes(1)

    try:
        db.delete(like)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting like: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "like deleted"}


@router.post("/tweet/repost/{tweet_id}")
def createRepost(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    tweet: Tweet = db.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    repost = TweetRepost(user.id, tweet_id)
    tweet.increment_reposts()

    try:
        db.add(repost)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating repost: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "repost created"}


@router.get("/tweet/repost")
def getReposts(
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    reposts = db.query(TweetRepost).filter_by(user_id=user.id).all()

    if not reposts:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [repost.to_dict() for repost in reposts]

    return {"result": res}


@router.delete("/tweet/repost/{tweet_id}")
def deleteRepost(
    tweet_id: str,
    user: UserToken = Depends(VerifyToken),
    db: Session = Depends(get_db),
):
    repost = db.query(TweetRepost).filter_by(id=tweet_id).first()

    if not repost:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(repost.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthorized")

    tweet = db.query(Tweet).filter_by(id=repost.tweet_id).first()
    if tweet:
        tweet.decrement_reposts()

    try:
        db.delete(repost)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting repost: {e}")
        raise HTTPException(status_code=500, detail="database error")

    return {"message": "repost deleted"}


@router.get("/test")
def testRoute(user: UserToken = Depends(VerifyToken)):
    logger.info(f"Received test request from user: {user.username}")

    return {"Hello": f"{user.username}"}
