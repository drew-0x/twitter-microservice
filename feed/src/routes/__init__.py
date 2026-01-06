import logging

import redis
from fastapi import APIRouter, Depends, Query

from src.dependencies.auth import UserToken, VerifyToken
from src.dependencies.redis import get_redis_client, get_feed_tweet_ids
from src.grpc.client import GetTweets


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/feed")
def get_feed(
    user: UserToken = Depends(VerifyToken),
    redis_conn: redis.Redis = Depends(get_redis_client),
    limit: int = Query(default=50, ge=1, le=100, description="Number of tweets to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """
    Get the authenticated user's personalized feed.

    The feed contains tweets from users they follow, ordered newest first.
    Feed data is populated by the feed-worker service via fan-out-on-write.
    """
    tweet_ids = get_feed_tweet_ids(redis_conn, user.id, limit=limit, offset=offset)

    if not tweet_ids:
        return {"tweets": [], "count": 0}

    tweets = GetTweets(tweet_ids)

    logger.info(f"Feed for user {user.id}: {len(tweets)} tweets returned")

    return {
        "tweets": tweets,
        "count": len(tweets),
        "limit": limit,
        "offset": offset,
    }


@router.get("/health")
def health_check():
    """Health check endpoint for load balancers and k8s probes."""
    return {"status": "healthy", "service": "feed-service"}
