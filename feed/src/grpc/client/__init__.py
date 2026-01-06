import logging

import grpc

from .user_service_pb2_grpc import UserStub
from .user_service_pb2 import (
    UserStruct,
    GetUserRes,
    GetUserReq,
    IncrementTweetsRes,
)

from src.grpc.server.tweet_service_pb2_grpc import TweetStub
from src.grpc.server.tweet_service_pb2 import GetTweetsReq, GetTweetsRes

from src.dependencies.config import config

logger = logging.getLogger(__name__)

USER_GRPC_TARGET = config.get("USER_SERVICE_GRPC_TARGET", "user-service:50051")
TWEET_GRPC_TARGET = config.get("TWEET_SERVICE_GRPC_TARGET", "tweet-service:50051")


def GetUser(user_id: str):
    try:
        with grpc.insecure_channel(USER_GRPC_TARGET) as channel:
            stub = UserStub(channel)
            response: GetUserRes = stub.GetUser(GetUserReq(user_id=user_id))

        logger.info(f"GetUser response for {user_id}: {response.valid}")
        return response.user
    except grpc.RpcError as e:
        logger.error(f"gRPC error in GetUser: {e.code()}: {e.details()}")
        return None


def GetTweets(tweet_ids: list[str]) -> list:
    """
    Fetch tweets by IDs from tweet service via gRPC.
    Returns list of tweet dicts.
    """
    if not tweet_ids:
        return []

    try:
        with grpc.insecure_channel(TWEET_GRPC_TARGET) as channel:
            stub = TweetStub(channel)
            response: GetTweetsRes = stub.GetTweets(GetTweetsReq(tweet_ids=tweet_ids))

        tweets = [
            {
                "id": tweet.id,
                "user_id": tweet.user_id,
                "content": tweet.content,
                "num_likes": tweet.num_likes,
                "num_replys": tweet.num_replys,
                "num_reposts": tweet.num_reposts,
                "created_at": tweet.created_at,
            }
            for tweet in response.tweets
        ]

        logger.info(f"GetTweets: fetched {len(tweets)} tweets")
        return tweets
    except grpc.RpcError as e:
        logger.error(f"gRPC error in GetTweets: {e.code()}: {e.details()}")
        return []
