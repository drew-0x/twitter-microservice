import grpc

# import src.proto.client.user_service_pb2_grpc as user_pb2_grpc

from .user_service_pb2_grpc import UserStub

from .user_service_pb2 import (
    UserStruct,
    GetUserRes,
    GetUserReq,
    IncrementTweetsRes,
)

# import src.proto.client.user_service_pb2 as user_pb2

from src.dependencies.config import config


USER_GRPC_TARGET = "user-service:50051"


def GetUser(user_id: str):
    with grpc.insecure_channel(USER_GRPC_TARGET) as channel:
        stub = UserStub(channel)
        response: GetUserRes = stub.GetUser(GetUserReq(user_id=user_id))

    print(response)

    return response.user


def IncrementTweets(user_id: str):
    with grpc.insecure_channel(USER_GRPC_TARGET) as channel:
        stub = UserStub(channel)
        response: IncrementTweetsRes = stub.IncrementsTweets(
            GetUserReq(user_id=user_id)
        )

    print(response)

    return response
