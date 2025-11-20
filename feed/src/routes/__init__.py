import logging
from os import stat

from fastapi import APIRouter, Depends, HTTPException

from src.dependencies.mq import produce_message

from sqlalchemy.exc import SQLAlchemyError

from src.grpc.client.user_service_pb2_grpc import User
from src.models import Tweet, TweetRepost, ReplyTweet, TweetLike

from src.grpc.client import IncrementTweets, GetUser

from src.dependencies.auth import UserToken, VerifyToken


from src.dependencies.db import db_session as DB
from src.schemas import CreateReplyRequest, CreateTweetRequest


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tweet")
def createTweet(req: CreateTweetRequest, user: UserToken = Depends(VerifyToken)):

    tweet = Tweet(user.id, req.content)

    try:
        DB.add(tweet)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    IncrementTweets(user.id)

    produce_message(tweet.to_dict(), "general_tweets")  # Produce to tweet feed queue

    produce_message(  # Produce to the tweet event queue
        tweet.to_dict(), "tweet_event", "tweet_created"
    )
    return ({"message": "tweet created"}), 201


@router.get("/tweet")
def getTweets(user: UserToken = Depends(VerifyToken)):
    tweets = DB.query(Tweet).filter_by(user_id=user.id).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="Invalid Request")

    res = [tweet.to_dict() for tweet in tweets]

    return {"result": res}


@router.get("/tweet/{tweet_id}")
def getTweetByID(tweet_id: str):

    tweet = DB.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    replyTweets = DB.query(ReplyTweet).filter_by(parent_id=tweet.id).all()

    replyTweetsRes = [tweet.to_dict() for tweet in replyTweets]

    return {"tweet": tweet.to_dict(), "replys": replyTweetsRes}


@router.delete("/tweet/{tweet_id}")
def deleteTweet(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    tweet = DB.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(tweet.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthroized")

    try:
        DB.delete(tweet)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "tweet deleted"}


@router.post("/tweet/reply")
def createTweetReply(req: CreateReplyRequest, user: UserToken = Depends(VerifyToken)):

    tweet = ReplyTweet(user.id, req.parent_id, req.content)

    try:
        DB.add(tweet)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    IncrementTweets(user.id)
    return {"message": "tweet created"}


@router.get("/tweet/reply")
def getTweetReplys(user: UserToken = Depends(VerifyToken)):
    tweets = DB.query(ReplyTweet).filter_by(user_id=user.id).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [tweet.to_dict() for tweet in tweets]

    return {"result": res}


@router.delete("/tweet/reply/{tweet_id}")
def deleteTweetReply(tweet_id: str, user: UserToken = Depends(VerifyToken)):

    tweet = DB.query(ReplyTweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(tweet.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthroized")

    try:
        DB.delete(tweet)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "tweet deleted"}


@router.post("/tweet/like/{tweet_id}")
def createLike(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    tweet: Tweet = DB.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    like = TweetLike(user.id, tweet_id)
    tweet.increment_likes()

    try:
        DB.add(like)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "like created"}


@router.route("/tweet/like")
def getLikes(user: UserToken = Depends(VerifyToken)):
    likes = DB.query(TweetLike).filter_by(user_id=user.id).all()

    if not likes:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [like.to_dict() for like in likes]

    return {"result": res}


@router.delete("/tweet/like/{tweet_id}")
def deleteLike(tweet_id: str, user: UserToken = Depends(VerifyToken)):

    like = DB.query(TweetLike).filter_by(id=tweet_id).first()

    if not like:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(like.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthroized")

    tweet = DB.query(Tweet).filter_by(id=like.tweet_id).first()
    if tweet:
        tweet.decrement_likes(1)

    try:
        DB.delete(like)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "like deleted"}


@router.post("/tweet/repost/{tweet_id}")
def createRepost(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    tweet: Tweet = DB.query(Tweet).filter_by(id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="invalid request")

    repost = TweetRepost(user.id, tweet_id)
    tweet.increment_reposts()

    try:
        DB.add(repost)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "repost created"}


@router.get("/tweet/repost")
def getReposts(user: UserToken = Depends(VerifyToken)):
    reposts = DB.query(TweetRepost).filter_by(user_id=user.id).all()

    if not reposts:
        raise HTTPException(status_code=404, detail="invalid request")

    res = [repost.to_dict() for repost in reposts]

    return {"result": res}


@router.delete("/tweet/repose/{tweet_id}")
def deleteRepost(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    repost = DB.query(TweetRepost).filter_by(id=tweet_id).first()

    if not repost:
        raise HTTPException(status_code=404, detail="invalid request")

    if str(repost.user_id) != user.id:
        raise HTTPException(status_code=403, detail="unauthroized")

    tweet = DB.query(Tweet).filter_by(id=repost.tweet_id).first()
    if tweet:
        tweet.decrement_reposts()

    try:
        DB.delete(repost)
        DB.commit()
    except SQLAlchemyError as e:
        DB.rollback()
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

    return {"message": "repost deleted"}


@router.get("/test")
def testRoute(user: UserToken = Depends(VerifyToken)):
    print(f"Recieved test request from uesr: {user.username}")

    return {"Hello": f"{user.username}"}
