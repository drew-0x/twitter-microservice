import logging
from contextlib import contextmanager
from concurrent import futures
from uuid import UUID
from typing import Generator

import grpc
from sqlalchemy.orm import Session

import src.grpc.user_service_pb2 as pb2
import src.grpc.user_service_pb2_grpc as pb2_grpc
from src.dependencies.db import SessionLocal
from src.models import User, Follow

logger = logging.getLogger(__name__)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions in gRPC handlers."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class UserService(pb2_grpc.UserServicer):
    def GetUser(self, request, context):
        with get_session() as db:
            userID = UUID(request.user_id, version=4)

            user = db.query(User).filter_by(id=userID).first()

            if not user:
                return pb2.GetUserRes(valid=False, user=None)

            user_struct = pb2.UserStruct(
                id=str(user.id),
                email=user.email,
                username=user.username,
                numTweets=user.num_tweets,
                numFollowers=user.num_followers,
                created_at=0,
            )
            return pb2.GetUserRes(valid=True, user=user_struct)

    def IncrementsTweets(self, request, context):
        with get_session() as db:
            userID = request.user_id

            user: User = db.query(User).filter_by(id=userID).first()

            if not user:
                return pb2.IncrementTweetsRes(success=False)

            user.increment_tweets()

            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error incrementing tweets: {e}")
                return pb2.IncrementTweetsRes(success=False)

            return pb2.IncrementTweetsRes(success=True)

    def GetFollowers(self, request, context):
        with get_session() as db:
            userID = request.user_id

            followers = db.query(Follow).filter_by(following_id=userID).all()

            if not followers:
                return pb2.GetFollowersRes(followers=None)

            followerRes = [
                pb2.FollowStruct(
                    id=str(follower.id),
                    follower_id=str(follower.follower_id),
                    following_id=str(follower.following_id),
                    created_at=0,
                )
                for follower in followers
            ]

            return pb2.GetFollowersRes(followers=followerRes)

    def GetFollowing(self, request, context):
        with get_session() as db:
            userID = request.user_id

            followers = db.query(Follow).filter_by(follower_id=userID).all()

            if not followers:
                return pb2.GetFollowersRes(followers=None)

            followerRes = [
                pb2.FollowStruct(
                    id=str(follower.id),
                    follower_id=str(follower.follower_id),
                    following_id=str(follower.following_id),
                    created_at=0,
                )
                for follower in followers
            ]

            return pb2.GetFollowersRes(followers=followerRes)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_UserServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
