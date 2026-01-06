# Week 1 Implementation Guide

**Timeline:** Days 1-7
**Focus:** Core functionality fixes and Feed Service implementation

---

## Table of Contents
- [Day 1-2: Quick Fixes & Database Optimization](#day-1-2-quick-fixes--database-optimization)
  - [Section A: Quick Bug Fixes](#section-a-quick-bug-fixes-4-items)
  - [Section B: Database Indexes](#section-b-database-indexes-4-items)
  - [Section D: Security Fixes](#section-d-security-fixes-4-items)
- [Day 3-7: Feed Service Implementation](#day-3-7-feed-service-implementation)
  - [Section E: Feed Service](#section-e-feed-service-implementation-10-items)

---

## Day 1-2: Quick Fixes & Database Optimization

### Section A: Quick Bug Fixes (4 items)

---

#### ✅ Item 1: Fix Routing Key Mismatch in Tweets Service

**File:** `tweets/src/routes/__init__.py` (line 43)

**The Problem:**
Your tweets service publishes to the search worker using routing key `"tweet_created"`, but the search-worker is listening for `"tweet.create"`. This mismatch means tweets never get indexed in Elasticsearch!

**Current Code (WRONG):**
```python
# Line 42-43 in tweets/src/routes/__init__.py
produce_message(  # Produce to the tweet event queue
    tweet.to_dict(), "tweet_event", "tweet_created"  # ❌ Wrong routing key
)
```

**Search Worker Expects:**
```go
// search-worker/main.go listens for "tweet.create"
switch d.RoutingKey {
case "tweet.create":
    // Handle tweet creation
}
```

**Fixed Code:**
```python
# Line 42-43 in tweets/src/routes/__init__.py
produce_message(  # Produce to the tweet event queue
    tweet.to_dict(), "tweet_events", "tweet.create"  # ✅ Correct routing key
)
```

**Changes to Make:**
1. Line 43: Change `"tweet_event"` → `"tweet_events"` (queue name)
2. Line 43: Change `"tweet_created"` → `"tweet.create"` (routing key)

**Why This Matters:**
Without this fix, the search service will never receive tweet creation events, meaning search will always return empty results even after you implement the search endpoints.

---

#### ✅ Item 2: Fix Typo in Delete Repost Endpoint

**File:** `tweets/src/routes/__init__.py` (line 232)

**The Problem:**
You have a typo in the URL: `/tweet/repose/` instead of `/tweet/repost/`. This breaks the API contract and looks unprofessional.

**Current Code (WRONG):**
```python
# Line 232
@router.delete("/tweet/repose/{tweet_id}")  # ❌ Typo: "repose" instead of "repost"
def deleteRepost(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    # ...
```

**Fixed Code:**
```python
# Line 232
@router.delete("/tweet/repost/{tweet_id}")  # ✅ Correct spelling
def deleteRepost(tweet_id: str, user: UserToken = Depends(VerifyToken)):
    # ...
```

**Why This Matters:**
- **Consistency:** You have `POST /tweet/repost/{id}` and `GET /tweet/repost`, but delete uses wrong spelling
- **API Contract:** Client applications calling `DELETE /tweet/repost/123` will get 404 errors
- **Resume Red Flag:** Typos in REST APIs show lack of attention to detail

---

#### ✅ Item 3: Fix Wrong Decorator for getLikes Endpoint

**File:** `tweets/src/routes/__init__.py` (line 163)

**The Problem:**
You're using `@router.route` instead of `@router.get`. The `route` decorator requires a `methods` parameter and is not the FastAPI way. This endpoint will fail!

**Current Code (WRONG):**
```python
# Line 163-164
@router.route("/tweet/like")  # ❌ Wrong decorator - this is Flask syntax!
def getLikes(user: UserToken = Depends(VerifyToken)):
    likes = DB.query(TweetLike).filter_by(user_id=user.id).all()
    # ...
```

**Error You'll Get:**
```
TypeError: route() missing 1 required positional argument: 'methods'
```

**Fixed Code:**
```python
# Line 163-164
@router.get("/tweet/like")  # ✅ Correct FastAPI decorator
def getLikes(user: UserToken = Depends(VerifyToken)):
    likes = DB.query(TweetLike).filter_by(user_id=user.id).all()
    # ...
```

**Why This Matters:**
This endpoint literally doesn't work right now. It will crash when called. This is a **critical bug** that would be caught in any code review.

---

#### ✅ Item 4: Fix Typo in gRPC Proto File

**File:** `proto/user_service.proto` (check if this typo exists)

**The Problem:**
The proto message might have `CreateFollowerRequset` instead of `CreateFollowerRequest` (missing 'e' in Request).

**If You Find This Typo:**
```protobuf
// WRONG
message CreateFollowerRequset {  // ❌ Typo
    string follower_id = 1;
}

// CORRECT
message CreateFollowerRequest {  // ✅ Fixed
    string follower_id = 1;
}
```

**After Fixing:**
You must regenerate gRPC code:
```bash
cd proto
python -m grpc_tools.protoc -I. --python_out=../users/src/grpc/client --grpc_python_out=../users/src/grpc/client user_service.proto
```

**Note:** I couldn't find this exact typo in your current proto file, but check carefully. If it doesn't exist, you can skip this item!

---

### Section B: Database Indexes (4 items)

**What are Database Indexes?**
Indexes are like a book's index - they help the database find data quickly without scanning every row. Without indexes, queries get slower as data grows.

---

#### ✅ Item 5: Add Unique Constraints to User Model

**File:** `users/src/models.py`

**The Problem:**
Currently, multiple users can register with the same email or username! This breaks authentication and user lookups.

**Current Code:**
```python
class User(Base):
    __tablename__ = "actors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, nullable=False)  # ❌ No unique constraint!
    password = Column(String, nullable=False)
    username = Column(String, nullable=False)  # ❌ No unique constraint!
    # ...
```

**Fixed Code:**
```python
class User(Base):
    __tablename__ = "actors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, nullable=False, unique=True)  # ✅ Added unique=True
    password = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)  # ✅ Added unique=True
    num_tweets = Column(INT, default=0)
    num_followers = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
```

**What This Does:**
- PostgreSQL creates a unique index on `email` and `username`
- Attempting to insert duplicate values raises `IntegrityError`
- Protects data integrity at the database level

**Testing After Change:**
```python
# This should raise an error on second insert:
user1 = User("test@email.com", "password123", "testuser")
user2 = User("test@email.com", "different_pw", "different_user")  # ❌ Will fail!
```

---

#### ✅ Item 6: Add Indexes to User Model

**File:** `users/src/models.py`

**The Problem:**
Queries like "find user by username" or "get recent users" do full table scans. With 1 million users, this takes seconds instead of milliseconds.

**Add These Indexes:**
```python
from sqlalchemy import Index

class User(Base):
    __tablename__ = "actors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, nullable=False, unique=True)  # unique=True creates an index automatically
    password = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)  # unique=True creates an index automatically
    num_tweets = Column(INT, default=0)
    num_followers = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Add explicit indexes (unique=True already creates indexes for email/username)
    __table_args__ = (
        Index('ix_users_created_at', 'created_at'),  # For sorting by signup date
    )
```

**Why These Indexes:**
- ✅ `email` - Already indexed by `unique=True` (for login queries)
- ✅ `username` - Already indexed by `unique=True` (for profile lookups)
- ➕ `created_at` - For "newest users" queries, sorting

**Performance Impact:**
- **Without index:** Query scans all 1M rows (~2 seconds)
- **With index:** Query uses index (~5 milliseconds)
- **400x faster!**

---

#### ✅ Item 7: Add Indexes to Follow Model

**File:** `users/src/models.py`

**The Problem:**
Queries like "get all followers" or "get all following" will be very slow without indexes.

**Current Code:**
```python
class Follow(Base):
    __tablename__ = "follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    follower_id = Column(UUID(as_uuid=True), nullable=False)  # ❌ No index
    following_id = Column(UUID(as_uuid=True), nullable=False)  # ❌ No index
    created_at = Column(DateTime, default=func.now(), nullable=False)  # ❌ No index
```

**Fixed Code:**
```python
from sqlalchemy import Index, UniqueConstraint

class Follow(Base):
    __tablename__ = "follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    follower_id = Column(UUID(as_uuid=True), nullable=False)
    following_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Add indexes and constraints
    __table_args__ = (
        # Prevent duplicate follows
        UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
        # Index for "who follows user X" queries
        Index('ix_follows_following_id', 'following_id'),
        # Index for "who does user X follow" queries
        Index('ix_follows_follower_id', 'follower_id'),
        # Index for sorting by follow date
        Index('ix_follows_created_at', 'created_at'),
    )
```

**Why These Indexes:**
1. **UniqueConstraint** - Prevents User A from following User B multiple times
2. **ix_follows_following_id** - Speeds up `GetFollowers(user_id)` (who follows me?)
3. **ix_follows_follower_id** - Speeds up `GetFollowing(user_id)` (who do I follow?)
4. **ix_follows_created_at** - For "newest followers" or "recently followed" queries

---

#### ✅ Item 8: Add Indexes to Tweet Model

**File:** `tweets/src/models.py`

**The Problem:**
Timeline queries ("get all tweets by user") and reply threading will be slow without indexes.

**Current Code:**
```python
class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # ❌ No index
    content = Column(String, nullable=False)
    num_likes = Column(INT, default=0)
    num_replys = Column(INT, default=0)
    num_reposts = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)  # ❌ No index
```

**Fixed Code:**
```python
from sqlalchemy import Index

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=False)
    num_likes = Column(INT, default=0)
    num_replys = Column(INT, default=0)
    num_reposts = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Add indexes
    __table_args__ = (
        Index('ix_tweets_user_id', 'user_id'),  # For user timeline queries
        Index('ix_tweets_created_at', 'created_at'),  # For sorting by recency
        # Composite index for user timeline sorted by date (most common query)
        Index('ix_tweets_user_created', 'user_id', 'created_at'),
    )


class ReplyTweet(Base):
    __tablename__ = "reply_tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=False)  # ❌ Needs index!
    content = Column(String, nullable=False)
    # ...

    # Add indexes
    __table_args__ = (
        Index('ix_reply_tweets_parent_id', 'parent_id'),  # For getting replies to a tweet
        Index('ix_reply_tweets_user_id', 'user_id'),
        Index('ix_reply_tweets_created_at', 'created_at'),
    )
```

**Why These Indexes:**
1. **user_id** - For "show all tweets by @username"
2. **created_at** - For timeline sorting (newest first)
3. **user_id + created_at composite** - Optimizes the most common query: "get user's tweets sorted by date"
4. **parent_id** (ReplyTweet) - For loading reply threads

**Similarly, add to TweetLike and TweetRepost:**
```python
class TweetLike(Base):
    # ... existing columns ...

    __table_args__ = (
        UniqueConstraint('user_id', 'tweet_id', name='unique_like'),  # Can't like twice
        Index('ix_tweet_like_user_id', 'user_id'),
        Index('ix_tweet_like_tweet_id', 'tweet_id'),
    )

class TweetRepost(Base):
    # ... existing columns ...

    __table_args__ = (
        UniqueConstraint('user_id', 'tweet_id', name='unique_repost'),  # Can't repost twice
        Index('ix_tweet_repost_user_id', 'user_id'),
        Index('ix_tweet_repost_tweet_id', 'tweet_id'),
    )
```

---

### Section D: Security Fixes (4 items)

---

#### ✅ Item 17: Generate Strong JWT_SECRET

**File:** `.env`

**The Problem:**
Your JWT_SECRET is literally `"test"`. Anyone can forge authentication tokens and impersonate users!

**Current .env File (INSECURE!):**
```bash
JWT_SECRET=test  # ❌ CRITICAL SECURITY VULNERABILITY!
JWT_ALGO=HS256
```

**How Bad Is This?**
An attacker can:
1. Create a JWT with `{"user_id": "admin", "username": "admin"}`
2. Sign it with secret `"test"`
3. Get full access to any user account

**Generate a Strong Secret:**
```bash
# Run this command in your terminal:
openssl rand -hex 32
```

**Example Output:**
```
a7f3d9e2b8c4f1a6d3e7b9c2f5a8d1e4b7c3f6a9d2e5b8c1f4a7d3e6b9c2f5a8
```

**Update .env File:**
```bash
JWT_SECRET=a7f3d9e2b8c4f1a6d3e7b9c2f5a8d1e4b7c3f6a9d2e5b8c1f4a7d3e6b9c2f5a8  # ✅ Strong 64-character secret
JWT_ALGO=HS256
```

**Important:**
- Never commit this to Git (`.env` should be in `.gitignore`)
- Use different secrets for dev/staging/production
- Rotate secrets periodically in production

---

#### ✅ Item 18: Add JWT Token Expiration

**File:** `users/src/dependencies/auth.py`

**The Problem:**
Your JWT tokens **never expire**. A stolen token works forever!

**Current Code (VULNERABLE):**
```python
# Line 29-35
def sign_jwt(user_id: str, username: str) -> str:
    token = jwt.encode(
        {"user_id": str(user_id), "username": username},  # ❌ No expiration!
        config["JWT_SECRET"],
        algorithm="HS256",
    )
    return token
```

**Fixed Code:**
```python
from datetime import datetime, timedelta

def sign_jwt(user_id: str, username: str) -> str:
    # Token expires in 24 hours
    expiration = datetime.utcnow() + timedelta(hours=24)

    token = jwt.encode(
        {
            "user_id": str(user_id),
            "username": username,
            "exp": expiration,  # ✅ Expiration time (Unix timestamp)
            "iat": datetime.utcnow()  # ✅ Issued at time
        },
        config["JWT_SECRET"],
        algorithm="HS256",
    )
    return token
```

**What Changed:**
1. Added `exp` claim - Token expires after 24 hours
2. Added `iat` claim - When token was issued (for audit logs)
3. Imported `datetime` and `timedelta`

**JWT Claims Explained:**
- `exp` (expiration time) - Unix timestamp when token expires
- `iat` (issued at) - Unix timestamp when token was created
- PyJWT automatically validates `exp` when decoding

---

#### ✅ Item 19: Update decode_jwt() to Validate Expiration

**File:** `users/src/dependencies/auth.py`

**The Problem:**
Your `decode_jwt()` catches all exceptions and returns `{}`, hiding token expiration errors!

**Current Code (BROKEN):**
```python
# Line 38-43
def decode_jwt(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, config["JWT_SECRET"], config["JWT_ALGO"])
        return decoded_token
    except Exception as e:  # ❌ Catches expiration errors and returns empty dict!
        return {}
```

**The Bug:**
- Expired tokens return `{}`
- `VerifyToken` then tries to access `payload["user_id"]`
- Gets `KeyError` instead of proper "token expired" message

**Fixed Code:**
```python
def decode_jwt(token: str) -> Dict:
    try:
        # PyJWT automatically validates 'exp' claim
        decoded_token = jwt.decode(
            token,
            config["JWT_SECRET"],
            algorithms=[config["JWT_ALGO"]]  # ✅ Changed to list format
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        # Let the caller handle this specific error
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        # Let the caller handle this specific error
        raise jwt.InvalidTokenError("Invalid token")
```

**What Changed:**
1. No longer returns `{}` on error
2. Raises specific exceptions that `VerifyToken` can catch
3. Changed `algorithms` parameter to list format (PyJWT requirement)

**Your `VerifyToken` Already Handles These:**
```python
# Line 46-63 - Already correct!
async def VerifyToken(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = decode_jwt(token)
        user_id: str = payload["user_id"]
        username: str = payload["username"]
        decoded_token = UserToken(user_id, username)
        return decoded_token

    except jwt.ExpiredSignatureError:  # ✅ This will now work!
        raise HTTPException(status_code=403, detail="Expired JWT Token")
    except jwt.InvalidTokenError:  # ✅ This will now work!
        raise HTTPException(status_code=403, detail="Invalid JWT Token")
```

---

#### ✅ Item 20: Summary of JWT Changes

**Complete Updated auth.py:**
```python
from dataclasses import dataclass
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.dependencies.config import Config
from src.models import User
from typing import Dict
from datetime import datetime, timedelta  # ✅ Add this import
import jwt

config = Config()
JWT_SECRET = config["JWT_SECRET"]
JWT_ALGO = config["JWT_ALGO"]
security = HTTPBearer()


@dataclass
class UserToken:
    id: str
    username: str


def sign_jwt(user_id: str, username: str) -> str:
    """Generate a JWT token with 24-hour expiration"""
    expiration = datetime.utcnow() + timedelta(hours=24)

    token = jwt.encode(
        {
            "user_id": str(user_id),
            "username": username,
            "exp": expiration,
            "iat": datetime.utcnow()
        },
        config["JWT_SECRET"],
        algorithm="HS256",
    )
    return token


def decode_jwt(token: str) -> Dict:
    """Decode and validate JWT token"""
    try:
        decoded_token = jwt.decode(
            token,
            config["JWT_SECRET"],
            algorithms=[config["JWT_ALGO"]]
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")


async def VerifyToken(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user information"""
    token = credentials.credentials

    try:
        payload = decode_jwt(token)
        user_id: str = payload["user_id"]
        username: str = payload["username"]
        decoded_token = UserToken(user_id, username)
        return decoded_token

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Expired JWT Token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid JWT Token")
```

---

## Day 3-7: Feed Service Implementation

### Section E: Feed Service Implementation (10 items)

**Architecture Overview:**
```
User requests feed → Feed Service → Redis (get tweet IDs) → Tweets gRPC (hydrate full data) → Return to user
```

---

#### ✅ Item 21: Implement GET /feed Endpoint

**File:** `feed/src/routes/__init__.py`

**The Problem:**
The file currently only has imports. No endpoints exist!

**Current Code:**
```python
# feed/src/routes/__init__.py (entire file)
import logging
from os import stat

from fastapi import APIRouter, Depends, HTTPException

from src.dependencies.mq import produce_message

from sqlalchemy.exc import SQLAlchemyError

from src.grpc.client.user_service_pb2_grpc import User
from src.models import Tweet, TweetRepost, ReplyTweet, TweetLike

from src.grpc.client import IncrementTweets, GetUser

from src.dependencies.auth import UserToken, VerifyToken


from src.dependencies.db import db_session as DB
from src.schemas import CreateReplyRequest, CreateTweetRequest


router = APIRouter()
logger = logging.getLogger(__name__)

# ❌ No routes defined!
```

**Create the Feed Endpoint:**
```python
# feed/src/routes/__init__.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from src.dependencies.auth import UserToken, VerifyToken
from src.services.feed_service import get_user_feed  # ✅ We'll create this next
from src.schemas import FeedResponse  # ✅ We'll create this too

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    user: UserToken = Depends(VerifyToken),
    limit: int = Query(default=20, ge=1, le=100),  # Min 1, max 100
    offset: int = Query(default=0, ge=0)
):
    """
    Get personalized feed for authenticated user

    Returns tweets from users that the authenticated user follows,
    sorted by creation time (newest first).

    - **limit**: Number of tweets to return (default: 20, max: 100)
    - **offset**: Number of tweets to skip for pagination (default: 0)
    """
    try:
        feed_data = await get_user_feed(user.id, limit, offset)
        return feed_data

    except Exception as e:
        logger.error(f"Error fetching feed for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch feed"
        )
```

**What This Does:**
1. Requires authentication (JWT token)
2. Accepts pagination parameters (`limit`, `offset`)
3. Validates `limit` is between 1-100
4. Calls `get_user_feed` service function (we'll implement next)
5. Returns typed response using Pydantic model

---

#### ✅ Item 22: Implement Redis Feed Retrieval Logic

**File:** Create `feed/src/services/feed_service.py`

**Create the Service Layer:**
```python
# feed/src/services/feed_service.py (NEW FILE)
import logging
from typing import List, Dict
import redis
import json
from src.dependencies.config import config

logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.Redis(
    host=config["REDIS_HOST"],
    port=int(config.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True  # Automatically decode bytes to strings
)


async def get_user_feed_ids(user_id: str, limit: int, offset: int) -> List[str]:
    """
    Fetch tweet IDs from user's Redis feed

    Redis stores feeds as sorted lists with key: "user_feed:{user_id}"
    Tweet IDs are stored newest-first

    Returns:
        List of tweet IDs (as strings)
    """
    feed_key = f"user_feed:{user_id}"

    try:
        # LRANGE gets elements from start to stop index
        # offset=0, limit=20 → get indices 0-19
        # offset=20, limit=20 → get indices 20-39
        end_index = offset + limit - 1

        tweet_ids = redis_client.lrange(feed_key, offset, end_index)

        logger.info(f"Retrieved {len(tweet_ids)} tweet IDs for user {user_id}")
        return tweet_ids

    except redis.RedisError as e:
        logger.error(f"Redis error fetching feed for user {user_id}: {str(e)}")
        return []  # Return empty list on error

    except Exception as e:
        logger.error(f"Unexpected error fetching feed: {str(e)}")
        return []
```

**How Redis Feed Works:**

1. **Feed Worker** pushes tweet IDs to Redis:
   ```python
   # When user tweets, feed-worker does:
   LPUSH user_feed:{follower_id} {tweet_id}
   ```

2. **Feed Service** reads tweet IDs:
   ```python
   LRANGE user_feed:{user_id} 0 19  # Get first 20 tweet IDs
   ```

3. **Redis Data Structure:**
   ```
   Key: "user_feed:123e4567-e89b-12d3-a456-426614174000"
   Value: [tweet_id_100, tweet_id_99, tweet_id_98, ...] (newest first)
   ```

---

#### ✅ Item 23: Create gRPC Client for Tweets Service

**File:** Create `feed/src/grpc/tweets_client.py`

**Why We Need This:**
Redis only stores tweet IDs. We need to call the Tweets service via gRPC to get full tweet data (content, likes, etc.)

**Step 1: Create tweets.proto (if doesn't exist)**

**File:** `proto/tweets.proto`
```protobuf
syntax = "proto3";

package tweets;

message Tweet {
    string id = 1;
    string user_id = 2;
    string content = 3;
    int32 num_likes = 4;
    int32 num_replys = 5;
    int32 num_reposts = 6;
    string created_at = 7;
}

message GetTweetsRequest {
    repeated string tweet_ids = 1;  // List of tweet IDs to fetch
}

message GetTweetsResponse {
    repeated Tweet tweets = 1;
}

service TweetService {
    rpc GetTweets(GetTweetsRequest) returns (GetTweetsResponse);
}
```

**Step 2: Generate Python gRPC Code**
```bash
cd proto
python -m grpc_tools.protoc -I. \
    --python_out=../feed/src/grpc/client \
    --grpc_python_out=../feed/src/grpc/client \
    tweets.proto
```

This creates:
- `feed/src/grpc/client/tweets_pb2.py`
- `feed/src/grpc/client/tweets_pb2_grpc.py`

**Step 3: Create gRPC Client Wrapper**

**File:** `feed/src/grpc/tweets_client.py`
```python
# feed/src/grpc/tweets_client.py (NEW FILE)
import grpc
import logging
from typing import List, Dict
from src.grpc.client import tweets_pb2, tweets_pb2_grpc
from src.dependencies.config import config

logger = logging.getLogger(__name__)

# gRPC connection settings
TWEETS_SERVICE_HOST = config.get("TWEETS_GRPC_HOST", "localhost")
TWEETS_SERVICE_PORT = config.get("TWEETS_GRPC_PORT", "50052")  # Different port!
TWEETS_SERVICE_ADDRESS = f"{TWEETS_SERVICE_HOST}:{TWEETS_SERVICE_PORT}"


def get_tweets_by_ids(tweet_ids: List[str]) -> List[Dict]:
    """
    Fetch full tweet data from Tweets service via gRPC

    Args:
        tweet_ids: List of tweet IDs to fetch

    Returns:
        List of tweet dictionaries
    """
    if not tweet_ids:
        return []

    try:
        # Create gRPC channel and stub
        with grpc.insecure_channel(TWEETS_SERVICE_ADDRESS) as channel:
            stub = tweets_pb2_grpc.TweetServiceStub(channel)

            # Create request
            request = tweets_pb2.GetTweetsRequest(tweet_ids=tweet_ids)

            # Call gRPC method
            response = stub.GetTweets(request)

            # Convert protobuf tweets to dictionaries
            tweets = []
            for tweet in response.tweets:
                tweets.append({
                    "id": tweet.id,
                    "user_id": tweet.user_id,
                    "content": tweet.content,
                    "num_likes": tweet.num_likes,
                    "num_replys": tweet.num_replys,
                    "num_reposts": tweet.num_reposts,
                    "created_at": tweet.created_at
                })

            logger.info(f"Fetched {len(tweets)} tweets via gRPC")
            return tweets

    except grpc.RpcError as e:
        logger.error(f"gRPC error fetching tweets: {e.code()} - {e.details()}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error in gRPC call: {str(e)}")
        return []
```

**Add to .env:**
```bash
TWEETS_GRPC_HOST=localhost  # or "tweets-service" in Docker
TWEETS_GRPC_PORT=50052
```

---

#### ✅ Item 24: Implement Feed Hydration Logic

**File:** `feed/src/services/feed_service.py` (add this function)

**Feed Hydration** = Converting tweet IDs to full tweet objects

**Add This Function:**
```python
# feed/src/services/feed_service.py (add to existing file)
from src.grpc.tweets_client import get_tweets_by_ids

async def get_user_feed(user_id: str, limit: int, offset: int) -> Dict:
    """
    Get user's personalized feed with full tweet data

    Process:
    1. Fetch tweet IDs from Redis (fast)
    2. Hydrate IDs into full tweet objects via gRPC (slower)
    3. Return paginated feed
    """
    # Step 1: Get tweet IDs from Redis
    tweet_ids = await get_user_feed_ids(user_id, limit, offset)

    if not tweet_ids:
        return {
            "tweets": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }

    # Step 2: Hydrate tweet IDs to full data via gRPC
    tweets = get_tweets_by_ids(tweet_ids)

    # Step 3: Get total feed count
    feed_key = f"user_feed:{user_id}"
    try:
        total_count = redis_client.llen(feed_key)
    except:
        total_count = len(tweets)

    # Step 4: Return structured response
    return {
        "tweets": tweets,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + len(tweets)) < total_count
    }
```

**Data Flow:**
```
1. Redis: ["tweet_id_1", "tweet_id_2", "tweet_id_3"]
2. gRPC Call: GetTweets(["tweet_id_1", "tweet_id_2", "tweet_id_3"])
3. Response: [
     {id: "tweet_id_1", content: "Hello world", ...},
     {id: "tweet_id_2", content: "Another tweet", ...},
     {id: "tweet_id_3", content: "Third tweet", ...}
   ]
```

---

#### ✅ Item 25: Add Pagination Support

**Already Implemented Above!**

The pagination is handled by:
1. `limit` and `offset` query parameters
2. Redis `LRANGE` command
3. `has_more` flag in response

**Example Usage:**
```bash
# Get first 20 tweets
GET /feed?limit=20&offset=0

# Get next 20 tweets
GET /feed?limit=20&offset=20

# Get 50 tweets starting at position 100
GET /feed?limit=50&offset=100
```

---

#### ✅ Item 26-28: Add GetTweets RPC to Tweets Service

**File:** `tweets/src/grpc/server.py`

**Step 1: Update tweets.proto (already done in Item 23)**

**Step 2: Implement GetTweets in Tweets gRPC Server**

```python
# tweets/src/grpc/server.py (add this method to your servicer class)
from src.models import Tweet
from src.dependencies.db import db_session as DB

class TweetServiceServicer(tweets_pb2_grpc.TweetServiceServicer):
    # ... existing methods ...

    def GetTweets(self, request, context):
        """
        Fetch multiple tweets by IDs (for feed hydration)
        """
        tweet_ids = request.tweet_ids

        if not tweet_ids:
            return tweets_pb2.GetTweetsResponse(tweets=[])

        try:
            # Query tweets from database
            tweets = DB.query(Tweet).filter(Tweet.id.in_(tweet_ids)).all()

            # Convert to protobuf messages
            tweet_messages = []
            for tweet in tweets:
                tweet_message = tweets_pb2.Tweet(
                    id=str(tweet.id),
                    user_id=str(tweet.user_id),
                    content=tweet.content,
                    num_likes=tweet.num_likes,
                    num_replys=tweet.num_replys,
                    num_reposts=tweet.num_reposts,
                    created_at=tweet.created_at.isoformat() if tweet.created_at else ""
                )
                tweet_messages.append(tweet_message)

            return tweets_pb2.GetTweetsResponse(tweets=tweet_messages)

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error fetching tweets: {str(e)}")
            return tweets_pb2.GetTweetsResponse(tweets=[])
```

**Step 3: Regenerate gRPC Code**
```bash
cd proto
python -m grpc_tools.protoc -I. \
    --python_out=../tweets/src/grpc/server \
    --grpc_python_out=../tweets/src/grpc/server \
    tweets.proto
```

---

#### ✅ Item 29: Create Pydantic Response Models

**File:** Create `feed/src/schemas.py`

```python
# feed/src/schemas.py (NEW FILE)
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TweetInFeed(BaseModel):
    """Individual tweet in feed"""
    id: str
    user_id: str
    content: str
    num_likes: int = 0
    num_replys: int = 0
    num_reposts: int = 0
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43f7-9abc-123456789def",
                "content": "This is a tweet in the feed!",
                "num_likes": 42,
                "num_replys": 3,
                "num_reposts": 7,
                "created_at": "2024-11-20T10:30:00"
            }
        }


class FeedResponse(BaseModel):
    """Paginated feed response"""
    tweets: List[TweetInFeed]
    total: int = Field(..., description="Total number of tweets in user's feed")
    limit: int = Field(..., description="Number of tweets returned")
    offset: int = Field(..., description="Starting position in feed")
    has_more: bool = Field(..., description="Whether more tweets are available")

    class Config:
        json_schema_extra = {
            "example": {
                "tweets": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "987fcdeb-51a2-43f7-9abc-123456789def",
                        "content": "First tweet",
                        "num_likes": 10,
                        "num_replys": 2,
                        "num_reposts": 1,
                        "created_at": "2024-11-20T10:30:00"
                    }
                ],
                "total": 157,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }
```

**What This Provides:**
- ✅ Type validation
- ✅ Automatic OpenAPI documentation
- ✅ JSON schema generation
- ✅ Example payloads in Swagger UI

---

#### ✅ Item 30: Add Error Handling

**File:** `feed/src/routes/__init__.py` (update)

**Enhanced Error Handling:**
```python
@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    user: UserToken = Depends(VerifyToken),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get personalized feed for authenticated user"""
    try:
        feed_data = await get_user_feed(user.id, limit, offset)

        # Handle empty feed
        if not feed_data.get("tweets"):
            logger.info(f"Empty feed for user {user.id}")
            # Return empty but valid response
            return {
                "tweets": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }

        return feed_data

    except redis.RedisError as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Feed service temporarily unavailable"
        )

    except grpc.RpcError as e:
        logger.error(f"gRPC error hydrating tweets: {e.code()} - {e.details()}")
        raise HTTPException(
            status_code=503,
            detail="Unable to load tweet details"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching feed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

**Error Scenarios Handled:**
1. ✅ Empty feed (new user, no followed users tweeting)
2. ✅ Redis connection failure
3. ✅ gRPC service unavailable
4. ✅ Tweet IDs exist but tweets deleted (returns partial results)
5. ✅ General exceptions

---

## Week 1 Completion Checklist

After completing all items above, verify:

- [ ] All 4 quick fixes applied (typos, routing keys, decorators)
- [ ] Database indexes added to all models
- [ ] Unique constraints on User.email and User.username
- [ ] JWT_SECRET changed from "test" to strong random string
- [ ] JWT tokens include `exp` and `iat` claims
- [ ] Feed service has `GET /feed` endpoint
- [ ] Feed service connects to Redis
- [ ] Feed service has gRPC client for Tweets service
- [ ] Tweets service has `GetTweets` RPC method
- [ ] Pydantic models for feed responses created
- [ ] Error handling for Redis/gRPC failures

---

## Testing Your Changes

### Test Feed Service Locally:

```bash
# 1. Start services
docker-compose up -d postgres redis rabbitmq

# 2. Start users service
cd users && python -m src.main

# 3. Start tweets service (on different port)
cd tweets && python -m src.main

# 4. Start feed service
cd feed && python -m src.main

# 5. Create a user and tweet
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'

# 6. Get JWT token from login
TOKEN="<your_jwt_token>"

# 7. Create a tweet
curl -X POST http://localhost:8001/tweet \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"My first tweet!"}'

# 8. Get feed
curl http://localhost:8002/feed \
  -H "Authorization: Bearer $TOKEN"
```

---

## Files Created This Week

**New Files:**
- `feed/src/services/feed_service.py`
- `feed/src/grpc/tweets_client.py`
- `feed/src/schemas.py`
- `proto/tweets.proto` (if didn't exist)

**Modified Files:**
- `users/src/models.py`
- `tweets/src/models.py`
- `tweets/src/routes/__init__.py`
- `tweets/src/grpc/server.py`
- `users/src/dependencies/auth.py`
- `feed/src/routes/__init__.py`
- `.env`

---

## Common Issues & Solutions

### Issue 1: Redis connection refused
**Solution:** Make sure Redis is running: `docker-compose up redis`

### Issue 2: gRPC connection refused
**Solution:** Check tweets service is running on port 50052 (not 50051)

### Issue 3: Empty feed despite tweets existing
**Solution:** Check feed-worker is running and consuming from `general_tweets` queue

### Issue 4: "Tweet IDs in Redis but GetTweets returns empty"
**Solution:** Verify tweets exist in database, check UUID format matching

### Issue 5: JWT exp claim not being validated
**Solution:** Make sure PyJWT version >= 2.0, update to `algorithms=["HS256"]` (list format)

---

**Next Week:** Week 2 - Database Migrations, Docker Configuration, and Testing

**Questions?** Review each section carefully and test as you go!
