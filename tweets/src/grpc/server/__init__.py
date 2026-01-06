import logging
from contextlib import contextmanager
from concurrent import futures
from typing import Generator

import grpc
from sqlalchemy.orm import Session

from .tweet_service_pb2 import TweetStruct, GetTweetsRes
from .tweet_service_pb2_grpc import TweetServicer, add_TweetServicer_to_server

from src.models import Tweet
from src.dependencies.db import SessionLocal

logger = logging.getLogger(__name__)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions in gRPC handlers."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TweetService(TweetServicer):
    def GetTweets(self, request, context):
        with get_session() as db:
            tweet_ids = request.tweet_ids

            if not tweet_ids:
                return GetTweetsRes(tweets=[])

            tweets = db.query(Tweet).filter(Tweet.id.in_(tweet_ids)).all()

            tweet_structs = [
                TweetStruct(
                    id=str(tweet.id),
                    user_id=str(tweet.user_id),
                    content=tweet.content,
                    num_likes=tweet.num_likes,
                    num_replys=tweet.num_replys,
                    num_reposts=tweet.num_reposts,
                    created_at=int(tweet.created_at.timestamp()),
                )
                for tweet in tweets
            ]

            logger.info(f"GetTweets: returning {len(tweet_structs)} tweets")
            return GetTweetsRes(tweets=tweet_structs)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_TweetServicer_to_server(TweetService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
