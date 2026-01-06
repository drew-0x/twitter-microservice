import logging

import grpc

from .user_service_pb2_grpc import UserStub

from .user_service_pb2 import (
    UserStruct,
    GetUserRes,
    GetUserReq,
    IncrementTweetsRes,
)

from src.dependencies.config import config

logger = logging.getLogger(__name__)

USER_GRPC_TARGET = config.get("USER_SERVICE_GRPC_TARGET", "user-service:50051")


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


def IncrementTweets(user_id: str):
    try:
        with grpc.insecure_channel(USER_GRPC_TARGET) as channel:
            stub = UserStub(channel)
            response: IncrementTweetsRes = stub.IncrementsTweets(
                GetUserReq(user_id=user_id)
            )

        logger.info(f"IncrementTweets response for {user_id}: {response.success}")
        return response
    except grpc.RpcError as e:
        logger.error(f"gRPC error in IncrementTweets: {e.code()}: {e.details()}")
        return None
