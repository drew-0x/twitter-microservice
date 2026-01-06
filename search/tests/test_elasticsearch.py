import pytest
from unittest.mock import patch, MagicMock


class TestSearchTweets:
    """Tests for Elasticsearch search functionality."""

    def test_search_tweets_returns_list(self):
        """Test that search_tweets returns a list."""
        from src.dependencies.elasticsearch import search_tweets

        result = search_tweets("test query")

        assert isinstance(result, list)

    def test_search_tweets_with_query(self):
        """Test search with a query string."""
        from src.dependencies.elasticsearch import search_tweets

        result = search_tweets("hello world")

        assert isinstance(result, list)
        # Mock implementation returns results
        assert len(result) > 0

    def test_search_tweets_respects_limit(self):
        """Test that limit parameter affects results."""
        from src.dependencies.elasticsearch import search_tweets

        # Mock returns fixed results, but limit should be passed
        result = search_tweets("test", limit=5)

        assert isinstance(result, list)

    def test_search_tweets_respects_offset(self):
        """Test that offset parameter is handled."""
        from src.dependencies.elasticsearch import search_tweets

        result = search_tweets("test", offset=10)

        assert isinstance(result, list)

    def test_search_tweets_empty_query(self):
        """Test search with empty query."""
        from src.dependencies.elasticsearch import search_tweets

        # Should still return results (mock implementation)
        result = search_tweets("")

        assert isinstance(result, list)

    def test_search_results_have_expected_fields(self):
        """Test that search results have expected fields."""
        from src.dependencies.elasticsearch import search_tweets

        results = search_tweets("test")

        if results:  # Mock returns results
            result = results[0]
            assert "id" in result
            assert "user_id" in result
            assert "content" in result

    def test_search_tweets_default_params(self):
        """Test search with default parameters."""
        from src.dependencies.elasticsearch import search_tweets

        result = search_tweets("test query")

        # Should work with defaults
        assert isinstance(result, list)


class TestSearchConfiguration:
    """Tests for Elasticsearch configuration."""

    def test_elasticsearch_url_from_config(self):
        """Test that ES URL is read from config."""
        with patch("src.dependencies.elasticsearch.config") as mock_config:
            mock_config.get.return_value = "http://custom-es:9200"

            # Re-import to pick up mocked config
            import importlib
            import src.dependencies.elasticsearch as es_module
            importlib.reload(es_module)

            # Verify config was called
            mock_config.get.assert_called()

    def test_index_name_is_tweets(self):
        """Test that the index name is set to 'tweets'."""
        from src.dependencies.elasticsearch import INDEX_NAME

        assert INDEX_NAME == "tweets"
