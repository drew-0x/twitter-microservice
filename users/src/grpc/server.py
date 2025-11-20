import grpc
from concurrent import futures

from uuid import UUID

import src.grpc.user_service_pb2 as pb2
import src.grpc.user_service_pb2_grpc as pb2_grpc
from src.dependencies.db import db_session as DB

from src.models import User
from src.models import Follow


class UserService(pb2_grpc.UserServicer):
    def GetUser(self, request, context):
        userID = UUID(request.user_id, version=4)

        user = User.query.filter_by(id=userID).first()

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
        res = pb2.GetUserRes(valid=True, user=user_struct)
        return res

    def IncrementsTweets(self, request, context):
        userID = request.user_id

        user: User = User.query.filter_by(id=userID).first()

        if not user:
            return pb2.IncrementTweetsRes(success=False)

        user.increment_tweets()

        try:
            DB.commit()
        except Exception as e:
            return pb2.IncrementTweetsRes(success=False)

        return pb2.IncrementTweetsRes(success=True)

    def GetFollowers(self, request, context):
        userID = request.user_id

        followers = Follow.query.filter_by(following_id=userID).all()

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
        userID = request.user_id

        followers = Follow.query.filter_by(follower_id=userID).all()

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
