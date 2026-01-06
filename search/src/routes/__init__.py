import logging

from fastapi import APIRouter, Depends, Query

from src.dependencies.auth import UserToken, VerifyToken
from src.dependencies.elasticsearch import (
    SearchClient,
    get_search_client,
    search_tweets,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    user: UserToken = Depends(VerifyToken),
    search_client: SearchClient = Depends(get_search_client),
):
    """
    Search tweets by content.

    Queries the Elasticsearch index populated by search-worker.
    """
    results = search_tweets(search_client, query=q, limit=limit, offset=offset)

    logger.info(f"Search for '{q}' by user {user.id}: {len(results)} results")

    return {
        "query": q,
        "results": results,
        "count": len(results),
        "limit": limit,
        "offset": offset,
    }


@router.get("/health")
def health_check():
    """Health check endpoint for load balancers and k8s probes."""
    return {"status": "healthy", "service": "search-service"}
