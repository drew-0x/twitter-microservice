import logging
from typing import Generator, Protocol

from src.dependencies.config import Config

logger = logging.getLogger(__name__)
config = Config()

ELASTICSEARCH_URL = config.get("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "tweets"


class SearchClient(Protocol):
    """Protocol for search client - allows for mock implementations."""

    def search(self, query: str, limit: int, offset: int) -> list[dict]:
        """Search tweets by query."""
        ...


class MockSearchClient:
    """Mock search client for development/testing."""

    def search(self, query: str, limit: int = 20, offset: int = 0) -> list[dict]:
        """Mock search that returns sample results."""
        logger.info(f"MOCK search: query='{query}', limit={limit}, offset={offset}")

        mock_results = [
            {
                "id": "mock-tweet-1",
                "user_id": "mock-user-1",
                "content": f"Mock tweet matching '{query}'",
                "score": 1.0,
            },
            {
                "id": "mock-tweet-2",
                "user_id": "mock-user-2",
                "content": f"Another mock result for '{query}'",
                "score": 0.8,
            },
        ]

        return mock_results


# Global search client instance
_search_client = MockSearchClient()


def get_search_client() -> Generator[SearchClient, None, None]:
    """
    FastAPI dependency that provides a search client.

    Usage:
        @router.get("/search")
        def search(client: SearchClient = Depends(get_search_client)):
            return client.search("query")
    """
    yield _search_client


def search_tweets(
    client: SearchClient,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Search tweets using the provided search client.

    Args:
        client: Search client instance
        query: Search query string
        limit: Max results to return
        offset: Offset for pagination

    Returns:
        List of tweet dicts matching the query
    """
    return client.search(query, limit, offset)
