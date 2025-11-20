from concurrent import futures
import grpc

# from src.proto import tweet_service_pb2
from .tweet_service_pb2 import TweetStruct, GetTweetsRes

# from src.proto import tweet_service_pb2_grpc
from .tweet_service_pb2_grpc import TweetServicer, add_TweetServicer_to_server
from src.models import Tweet


class TweetService(TweetServicer):
    def GetTweets(self, request, context):
        tweet_ids = request.tweet_ids
        tweets = Tweet.query.filter(Tweet.id.in_(tweet_ids)).all()
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
        return GetTweetsRes(tweets=tweet_structs)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_TweetServicer_to_server(TweetService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
