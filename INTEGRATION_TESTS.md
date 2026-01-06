# Integration Tests Guide

This document describes the integration tests you need to implement for the Twitter microservices project. Integration tests verify that multiple components work together correctly, including real database connections, message queues, and service-to-service communication.

## Prerequisites

Before running integration tests, ensure you have:

1. **Docker Compose** - For spinning up infrastructure
2. **pytest** and **pytest-asyncio** - Test framework
3. **httpx** - For async HTTP client testing

```bash
# Install test dependencies (add to each service's pyproject.toml)
pip install pytest pytest-asyncio httpx testcontainers
```

---

## Test Infrastructure Setup

### Docker Compose for Tests

Create `docker-compose.test.yml`:

```yaml
version: '3.8'
services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  rabbitmq-test:
    image: rabbitmq:3-management
    ports:
      - "5673:5672"
      - "15673:15672"
    environment:
      RABBITMQ_DEFAULT_USER: test
      RABBITMQ_DEFAULT_PASS: test
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5

  elasticsearch-test:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9201:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health"]
      interval: 10s
      timeout: 10s
      retries: 10
```

### Running Test Infrastructure

```bash
# Start test infrastructure
docker-compose -f docker-compose.test.yml up -d

# Wait for health checks
docker-compose -f docker-compose.test.yml ps

# Run tests
pytest tests/integration/ -v

# Teardown
docker-compose -f docker-compose.test.yml down -v
```

---

## Integration Tests to Implement

### 1. Users Service Integration Tests

**File:** `users/tests/integration/test_user_flow.py`

| Test | Description | Components |
|------|-------------|------------|
| `test_user_registration_persists_to_db` | Register user and verify in PostgreSQL | API → PostgreSQL |
| `test_user_login_with_registered_user` | Register then login with same credentials | API → PostgreSQL |
| `test_password_hashing_verification` | Verify bcrypt hashing works end-to-end | API → PostgreSQL |
| `test_duplicate_email_rejected` | Attempt duplicate registration | API → PostgreSQL |
| `test_duplicate_username_rejected` | Attempt duplicate username | API → PostgreSQL |
| `test_follow_creates_relationship` | Create follow and verify in DB | API → PostgreSQL |
| `test_follow_increments_follower_count` | Verify counter increment | API → PostgreSQL |
| `test_unfollow_removes_relationship` | Unfollow and verify deletion | API → PostgreSQL |

**Example Implementation:**

```python
# users/tests/integration/test_user_flow.py
import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "postgresql://test:test@localhost:5433/test_db"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
async def client():
    from src import App
    app = App()
    async with AsyncClient(app=app.app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_user_registration_persists_to_db(client, db_session):
    """Test that user registration creates a database record."""
    response = await client.post("/users/register", json={
        "email": "integration@test.com",
        "password": "testpass123",
        "username": "integrationuser"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify in database
    from src.models import User
    user = db_session.query(User).filter_by(email="integration@test.com").first()
    assert user is not None
    assert user.username == "integrationuser"

@pytest.mark.asyncio
async def test_login_returns_valid_jwt(client):
    """Test that login returns a JWT that can be used for auth."""
    # Register first
    await client.post("/users/register", json={
        "email": "login@test.com",
        "password": "testpass123",
        "username": "loginuser"
    })

    # Login
    response = await client.post("/users/login", json={
        "email": "login@test.com",
        "password": "testpass123"
    })

    assert response.status_code == 200
    token = response.json()["token"]

    # Use token to access protected endpoint
    response = await client.get(
        "/hello",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

### 2. Tweets Service Integration Tests

**File:** `tweets/tests/integration/test_tweet_flow.py`

| Test | Description | Components |
|------|-------------|------------|
| `test_create_tweet_persists_to_db` | Create tweet and verify in PostgreSQL | API → PostgreSQL |
| `test_create_tweet_publishes_to_rabbitmq` | Verify message in general_tweets queue | API → RabbitMQ |
| `test_create_tweet_calls_user_grpc` | Verify IncrementTweets gRPC called | API → gRPC → Users |
| `test_get_tweet_by_id` | Retrieve specific tweet | API → PostgreSQL |
| `test_delete_tweet_removes_from_db` | Delete tweet and verify removal | API → PostgreSQL |
| `test_like_tweet_increments_count` | Like tweet and verify counter | API → PostgreSQL |
| `test_unlike_tweet_decrements_count` | Unlike and verify decrement | API → PostgreSQL |
| `test_repost_tweet_creates_record` | Repost and verify in DB | API → PostgreSQL |
| `test_reply_links_to_parent` | Reply and verify parent_id | API → PostgreSQL |

**Example Implementation:**

```python
# tweets/tests/integration/test_tweet_flow.py
import pytest
import pika
from httpx import AsyncClient

RABBITMQ_URL = "amqp://test:test@localhost:5673/"

@pytest.fixture
def rabbitmq_channel():
    connection = pika.BlockingConnection(
        pika.URLParameters(RABBITMQ_URL)
    )
    channel = connection.channel()
    channel.queue_declare(queue='general_tweets')
    channel.queue_purge(queue='general_tweets')
    yield channel
    connection.close()

@pytest.mark.asyncio
async def test_create_tweet_publishes_to_rabbitmq(client, auth_token, rabbitmq_channel):
    """Test that creating a tweet publishes to RabbitMQ."""
    response = await client.post(
        "/tweet",
        json={"content": "Integration test tweet"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

    # Check RabbitMQ for message
    method, properties, body = rabbitmq_channel.basic_get(
        queue='general_tweets',
        auto_ack=True
    )

    assert body is not None
    import json
    message = json.loads(body)
    assert message["content"] == "Integration test tweet"
```

---

### 3. Feed Service Integration Tests

**File:** `feed/tests/integration/test_feed_flow.py`

| Test | Description | Components |
|------|-------------|------------|
| `test_feed_reads_from_redis` | Get feed with pre-populated Redis data | API → Redis |
| `test_feed_hydrates_tweets_via_grpc` | Verify gRPC calls to tweet service | API → Redis → gRPC |
| `test_feed_pagination` | Test limit/offset with Redis data | API → Redis |
| `test_empty_feed_for_new_user` | New user gets empty feed | API → Redis |
| `test_feed_order_is_newest_first` | Verify chronological order | API → Redis → gRPC |

**Example Implementation:**

```python
# feed/tests/integration/test_feed_flow.py
import pytest
import redis
from httpx import AsyncClient

REDIS_URL = "redis://localhost:6380"

@pytest.fixture
def redis_client():
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    client.flushdb()  # Clean up after test

@pytest.mark.asyncio
async def test_feed_reads_from_redis(client, auth_token, redis_client, user_id):
    """Test that feed reads tweet IDs from Redis."""
    # Pre-populate Redis
    feed_key = f"feed:{user_id}"
    redis_client.lpush(feed_key, "tweet-3", "tweet-2", "tweet-1")

    response = await client.get(
        "/feed",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3

@pytest.mark.asyncio
async def test_feed_pagination(client, auth_token, redis_client, user_id):
    """Test feed pagination with limit and offset."""
    feed_key = f"feed:{user_id}"
    # Add 10 tweets
    for i in range(10):
        redis_client.lpush(feed_key, f"tweet-{i}")

    # Get first page
    response = await client.get(
        "/feed?limit=5&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()
    assert len(data["tweets"]) <= 5

    # Get second page
    response = await client.get(
        "/feed?limit=5&offset=5",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()
    assert data["offset"] == 5
```

---

### 4. Search Service Integration Tests

**File:** `search/tests/integration/test_search_flow.py`

| Test | Description | Components |
|------|-------------|------------|
| `test_search_queries_elasticsearch` | Search returns ES results | API → Elasticsearch |
| `test_search_pagination` | Test limit/offset with ES | API → Elasticsearch |
| `test_search_relevance_scoring` | Verify results ordered by score | API → Elasticsearch |
| `test_search_empty_results` | Search with no matches | API → Elasticsearch |
| `test_search_special_characters` | Handle special chars in query | API → Elasticsearch |

**Example Implementation:**

```python
# search/tests/integration/test_search_flow.py
import pytest
from elasticsearch import Elasticsearch
from httpx import AsyncClient

ES_URL = "http://localhost:9201"

@pytest.fixture
def es_client():
    client = Elasticsearch([ES_URL])
    # Create test index
    if client.indices.exists(index="tweets"):
        client.indices.delete(index="tweets")
    client.indices.create(index="tweets")
    yield client
    client.indices.delete(index="tweets")

@pytest.fixture
def indexed_tweets(es_client):
    """Pre-index some tweets for testing."""
    tweets = [
        {"id": "1", "user_id": "u1", "content": "Hello world"},
        {"id": "2", "user_id": "u2", "content": "Hello there"},
        {"id": "3", "user_id": "u3", "content": "Goodbye world"},
    ]
    for tweet in tweets:
        es_client.index(index="tweets", id=tweet["id"], document=tweet)
    es_client.indices.refresh(index="tweets")
    return tweets

@pytest.mark.asyncio
async def test_search_queries_elasticsearch(client, auth_token, indexed_tweets):
    """Test that search queries Elasticsearch."""
    response = await client.get(
        "/search?q=hello",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should find "Hello world" and "Hello there"
    assert data["count"] >= 2
```

---

### 5. End-to-End Flow Tests

**File:** `tests/e2e/test_full_flow.py`

| Test | Description | Services |
|------|-------------|----------|
| `test_tweet_appears_in_follower_feed` | Full fan-out flow | Users → Tweets → RabbitMQ → Feed Worker → Redis → Feed |
| `test_tweet_indexed_for_search` | Full search indexing | Tweets → RabbitMQ → Search Worker → ES → Search |
| `test_user_signup_to_first_tweet` | Complete new user journey | Users → Tweets |
| `test_follow_unfollow_updates_counts` | Follow relationship flow | Users (gRPC) |

**Example Implementation:**

```python
# tests/e2e/test_full_flow.py
import pytest
import time
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tweet_appears_in_follower_feed(
    users_client, tweets_client, feed_client
):
    """
    End-to-end test: Tweet from followed user appears in feed.

    Flow:
    1. User A registers
    2. User B registers
    3. User B follows User A
    4. User A creates tweet
    5. Feed worker processes (wait)
    6. User B's feed contains the tweet
    """
    # 1. Register User A
    resp = await users_client.post("/users/register", json={
        "email": "usera@test.com",
        "password": "pass123",
        "username": "usera"
    })
    user_a_token = resp.json()["token"]
    user_a_id = resp.json()["user"]["id"]

    # 2. Register User B
    resp = await users_client.post("/users/register", json={
        "email": "userb@test.com",
        "password": "pass123",
        "username": "userb"
    })
    user_b_token = resp.json()["token"]

    # 3. User B follows User A
    await users_client.post(
        "/follow",
        json={"following_id": user_a_id},
        headers={"Authorization": f"Bearer {user_b_token}"}
    )

    # 4. User A creates tweet
    await tweets_client.post(
        "/tweet",
        json={"content": "Hello from User A!"},
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    # 5. Wait for feed worker to process
    time.sleep(2)  # In real tests, use polling or events

    # 6. Check User B's feed
    resp = await feed_client.get(
        "/feed",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )

    assert resp.status_code == 200
    tweets = resp.json()["tweets"]
    assert any(t["content"] == "Hello from User A!" for t in tweets)
```

---

### 6. gRPC Integration Tests

**File:** `tests/integration/test_grpc.py`

| Test | Description | Services |
|------|-------------|----------|
| `test_get_user_grpc` | Call GetUser and verify response | Tweets/Feed → Users gRPC |
| `test_increment_tweets_grpc` | Call IncrementTweets and verify DB | Tweets → Users gRPC |
| `test_get_followers_grpc` | Call GetFollowers with data | Feed Worker → Users gRPC |
| `test_get_tweets_grpc` | Call GetTweets and verify response | Feed → Tweets gRPC |
| `test_grpc_error_handling` | Verify error handling for failures | Any → gRPC |

**Example Implementation:**

```python
# tests/integration/test_grpc.py
import pytest
import grpc

@pytest.fixture
def user_grpc_stub():
    channel = grpc.insecure_channel("localhost:50051")
    from src.grpc.client.user_service_pb2_grpc import UserStub
    return UserStub(channel)

def test_get_user_grpc(user_grpc_stub, registered_user_id):
    """Test GetUser gRPC method."""
    from src.grpc.client.user_service_pb2 import GetUserReq

    request = GetUserReq(user_id=registered_user_id)
    response = user_grpc_stub.GetUser(request)

    assert response.valid is True
    assert response.user.id == registered_user_id

def test_grpc_nonexistent_user(user_grpc_stub):
    """Test GetUser with non-existent user."""
    from src.grpc.client.user_service_pb2 import GetUserReq

    request = GetUserReq(user_id="nonexistent-uuid")
    response = user_grpc_stub.GetUser(request)

    assert response.valid is False
```

---

## Running Integration Tests

### Command Reference

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific service's integration tests
pytest users/tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run with markers
pytest -m "integration" -v

# Run E2E tests (requires all services running)
pytest tests/e2e/ -v --tb=short
```

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: Integration tests requiring external services
    e2e: End-to-end tests requiring full system
    slow: Tests that take longer than 5 seconds
asyncio_mode = auto
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

      rabbitmq:
        image: rabbitmq:3
        ports:
          - 5672:5672

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
          RABBITMQ_URL: amqp://guest:guest@localhost:5672/
        run: pytest tests/integration/ -v
```

---

## Test Data Management

### Fixtures for Test Data

```python
# tests/fixtures.py
import pytest
from uuid import uuid4

@pytest.fixture
def test_user():
    return {
        "id": str(uuid4()),
        "email": f"test-{uuid4()}@example.com",
        "username": f"user-{uuid4().hex[:8]}",
        "password": "testpass123"
    }

@pytest.fixture
def test_tweet(test_user):
    return {
        "id": str(uuid4()),
        "user_id": test_user["id"],
        "content": "Test tweet content"
    }
```

### Database Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_db(db_session):
    """Clean up database after each test."""
    yield
    # Rollback any uncommitted changes
    db_session.rollback()
    # Optionally truncate tables
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
```

---

## Troubleshooting

### Common Issues

1. **Connection refused to services**
   - Ensure Docker containers are running and healthy
   - Check port mappings match test configuration

2. **gRPC tests failing**
   - Verify gRPC server is started before tests
   - Check proto files are compiled and in sync

3. **RabbitMQ messages not appearing**
   - Verify queue names match between producer and consumer
   - Check message acknowledgment settings

4. **Elasticsearch tests timing out**
   - ES takes time to start; increase wait time
   - Ensure index is refreshed after indexing documents

---

## Next Steps

1. Implement the test files described above
2. Add `pytest-cov` for coverage reporting
3. Set up CI/CD pipeline with GitHub Actions
4. Add performance/load testing with Locust (existing in `tests/locust-tests/`)
