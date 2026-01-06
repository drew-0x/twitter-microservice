# Phase 1: Implementation Checklist

**Goal:** Make the project functional and production-ready for resume inclusion

**Estimated Time:** 2 weeks

---

## Quick Reference

- **Total Items:** 56
- **Quick Fixes:** 4 items
- **Database Indexes:** 4 items
- **Database Migrations:** 8 items
- **Security Fixes:** 4 items
- **Feed Service:** 10 items
- **Search Service:** 8 items
- **Docker & Deployment:** 13 items
- **Testing & Validation:** 4 items

---

## A. Quick Fixes (4 items) - Start here, easy wins

- [ ] 1. Fix routing key mismatch in tweets service - change 'tweet_event' to 'tweet.create' in `tweets/src/utils/message_queue.py`
- [ ] 2. Fix typo in tweets service - rename `/tweet/repose/{tweet_id}` to `/tweet/repost/{tweet_id}` in `tweets/src/routes/__init__.py:232`
- [ ] 3. Fix wrong decorator in tweets service - change `@router.route` to `@router.get` for getLikes endpoint in `tweets/src/routes/__init__.py:163`
- [ ] 4. Fix typo in users gRPC proto - rename `CreateFollowerRequset` to `CreateFollowerRequest` in `proto/users.proto`

---

## B. Database Indexes (4 items) - Do before migrations

- [ ] 5. Add unique constraints on User model for username and email fields in `users/src/models.py`
- [ ] 6. Add database indexes to User model (username, email, created_at) in `users/src/models.py`
- [ ] 7. Add database indexes to Follow model (follower_id, following_id, created_at) in `users/src/models.py`
- [ ] 8. Add database indexes to Tweet model (user_id, created_at, parent_tweet_id) in `tweets/src/models.py`

---

## C. Database Migrations Setup (8 items) - Critical for production

### Users Service

- [ ] 9. Install Alembic in users service - add `alembic` to `users/pyproject.toml` dependencies
- [ ] 10. Initialize Alembic in users service - run `cd users && alembic init alembic` and configure `alembic.ini`
- [ ] 11. Create initial migration for users service - users and follows tables
- [ ] 12. Update users service `init_db()` to use Alembic instead of `create_all()` in `users/src/dependencies/db.py`

### Tweets Service

- [ ] 13. Install Alembic in tweets service - add `alembic` to `tweets/pyproject.toml` dependencies
- [ ] 14. Initialize Alembic in tweets service - run `cd tweets && alembic init alembic` and configure `alembic.ini`
- [ ] 15. Create initial migration for tweets service - tweets, replies, likes, reposts tables
- [ ] 16. Update tweets service `init_db()` to use Alembic instead of `create_all()` in `tweets/src/dependencies/db.py`

---

## D. Security Fixes (4 items) - Critical!

- [ ] 17. Generate strong JWT_SECRET and update `.env` file with secure value (use `openssl rand -hex 32`)
- [ ] 18. Add JWT token expiration - update `create_jwt()` to include `exp` claim (24 hours) in `users/src/dependencies/auth.py`
- [ ] 19. Update `decode_jwt()` to validate token expiration and raise proper errors in `users/src/dependencies/auth.py`
- [ ] 20. Add JWT `iat` (issued_at) claim to `create_jwt()` function in `users/src/dependencies/auth.py`

---

## E. Feed Service Implementation (10 items) - Core feature

### Backend Logic

- [ ] 21. Implement `GET /feed` endpoint in feed service routes - accept user_id from JWT, limit, offset params in `feed/src/routes/__init__.py`
- [ ] 22. Implement Redis feed retrieval logic in feed service - fetch tweet IDs from Redis list (create `feed/src/services/feed_service.py`)
- [ ] 23. Create gRPC client for tweets service in feed service - add GetTweets RPC method (create `feed/src/grpc/tweets_client.py`)
- [ ] 24. Implement feed hydration logic - call tweets gRPC service to get full tweet data from IDs in `feed/src/services/feed_service.py`
- [ ] 25. Add pagination support to `GET /feed` endpoint - limit default 20, max 100

### Tweets Service Updates

- [ ] 26. Add `GetTweets` RPC method to tweets service gRPC server - accept list of tweet IDs in `tweets/src/grpc/server.py`
- [ ] 27. Update `tweets.proto` file with GetTweets method definition in `proto/tweets.proto`
- [ ] 28. Regenerate gRPC code for tweets service after proto update (run protoc command)

### Polish

- [ ] 29. Create Pydantic response models for feed endpoint - FeedResponse, TweetInFeed in `feed/src/schemas.py`
- [ ] 30. Add error handling for empty feeds and missing tweets in feed service

---

## F. Search Service Implementation (8 items) - Core feature

### Elasticsearch Setup

- [ ] 31. Create Elasticsearch index mapping for tweets in search service - define fields (id, content, user_id, created_at, etc.) in `search/src/services/search_service.py`
- [ ] 32. Implement index initialization on search service startup - create tweets index if not exists in `search/src/main.py`

### Search Logic

- [ ] 33. Implement `GET /search` endpoint in search service - accept query, limit, offset params in `search/src/routes/__init__.py`
- [ ] 34. Implement Elasticsearch query logic in search service - full-text search on tweet content in `search/src/services/search_service.py`
- [ ] 35. Add pagination to search endpoint - limit default 20, max 100
- [ ] 36. Create Pydantic response models for search endpoint - SearchResponse, TweetSearchResult in `search/src/schemas.py`
- [ ] 37. Add search result highlighting in Elasticsearch query - highlight matching terms
- [ ] 38. Add error handling for Elasticsearch connection failures in search service

---

## G. Docker & Deployment (13 items) - Infrastructure

### Add Missing Services

- [ ] 39. Add feed-service to `docker-compose.yml` - configure ports, dependencies, environment
- [ ] 40. Add feed-worker to `docker-compose.yml` - configure dependencies on RabbitMQ and Redis

### Fix Port Conflicts

- [ ] 41. Fix gRPC port conflicts in `docker-compose.yml` - assign unique ports (users:50051, tweets:50052, feed:50053)
- [ ] 42. Update service gRPC server configurations to use assigned ports from docker-compose
- [ ] 43. Update gRPC client configurations to connect to correct service ports

### Improvements

- [ ] 44. Add restart policies to all services in `docker-compose.yml` - `restart: unless-stopped`
- [ ] 45. Add resource limits to services in `docker-compose.yml` - memory and CPU limits
- [ ] 46. Fix Go version in search-worker Dockerfile - change `FROM golang:1.25` to `golang:1.22`
- [ ] 47. Create `.dockerignore` files for all services to exclude unnecessary files

### Health Checks

- [ ] 48. Add health check endpoint `GET /health` to users service in `users/src/routes/health.py`
- [ ] 49. Add health check endpoint `GET /health` to tweets service in `tweets/src/routes/health.py`
- [ ] 50. Add health check endpoint `GET /health` to feed service in `feed/src/routes/health.py`
- [ ] 51. Add health check endpoint `GET /health` to search service in `search/src/routes/health.py`
- [ ] 52. Update `docker-compose.yml` to add healthcheck configurations for all Python services

---

## H. Testing & Validation (4 items) - Verify everything works

- [ ] 53. Test feed service locally - verify `GET /feed` returns paginated feed data
- [ ] 54. Test search service locally - verify `GET /search` returns relevant tweets
- [ ] 55. Test full workflow - register user, create tweet, verify feed updates, search for tweet
- [ ] 56. Verify all services start successfully with `docker-compose up`

---

## Recommended Implementation Order

### Week 1 - Core Functionality

**Day 1-2: Foundation**
- [ ] Complete Section A (Quick Fixes) - 4 items
- [ ] Complete Section B (Database Indexes) - 4 items
- [ ] Complete Section D (Security Fixes) - 4 items

**Day 3-4: Feed Service**
- [ ] Complete Section E (Feed Service Implementation) - 10 items

**Day 5-7: Search Service**
- [ ] Complete Section F (Search Service Implementation) - 8 items

### Week 2 - Production Ready

**Day 1-2: Database Migrations**
- [ ] Complete Section C (Database Migrations Setup) - 8 items

**Day 3-4: Infrastructure**
- [ ] Complete Section G (Docker & Deployment) - 13 items

**Day 5: Validation**
- [ ] Complete Section H (Testing & Validation) - 4 items

---

## Key Dependencies

⚠️ **Important: Follow these dependencies to avoid rework**

1. **Do B before C** - Add indexes to models before creating migrations
2. **Do E.26-28 before E.23** - Update tweets gRPC proto before creating feed client
3. **Do G.41-43 together** - Fix all port conflicts at once
4. **Do H last** - Test after everything is implemented

---

## File Reference Guide

### Quick Fixes
- `tweets/src/routes/__init__.py` - items 2, 3
- `tweets/src/utils/message_queue.py` - item 1
- `proto/users.proto` - item 4

### Database Models
- `users/src/models.py` - items 5, 6, 7
- `tweets/src/models.py` - item 8

### Migrations
- `users/pyproject.toml` - item 9
- `tweets/pyproject.toml` - item 13
- `users/alembic/` - items 10-12 (new directory)
- `tweets/alembic/` - items 14-16 (new directory)
- `users/src/dependencies/db.py` - item 12
- `tweets/src/dependencies/db.py` - item 16

### Security
- `.env` - item 17
- `users/src/dependencies/auth.py` - items 18-20

### Feed Service
- `feed/src/routes/__init__.py` - items 21, 25, 29, 30
- `feed/src/services/feed_service.py` - items 22, 24 (new file)
- `feed/src/grpc/tweets_client.py` - item 23 (new file)
- `feed/src/schemas.py` - item 29 (new file)
- `proto/tweets.proto` - items 26, 27

### Tweets Service gRPC Updates
- `tweets/src/grpc/server.py` - item 26
- `proto/tweets.proto` - item 27

### Search Service
- `search/src/routes/__init__.py` - items 33, 35, 36, 38
- `search/src/services/search_service.py` - items 31, 32, 34, 37 (new file)
- `search/src/schemas.py` - item 36 (new file)
- `search/src/main.py` - item 32

### Docker
- `docker-compose.yml` - items 39-45, 52
- `search-worker/Dockerfile` - item 46
- `.dockerignore` - item 47 (new files in each service directory)
- `users/src/routes/health.py` - item 48 (new file)
- `tweets/src/routes/health.py` - item 49 (new file)
- `feed/src/routes/health.py` - item 50 (new file)
- `search/src/routes/health.py` - item 51 (new file)

---

## Progress Tracking

**Completion Status:**
- [ ] A. Quick Fixes (0/4)
- [ ] B. Database Indexes (0/4)
- [ ] C. Database Migrations (0/8)
- [ ] D. Security Fixes (0/4)
- [ ] E. Feed Service (0/10)
- [ ] F. Search Service (0/8)
- [ ] G. Docker & Deployment (0/13)
- [ ] H. Testing & Validation (0/4)

**Overall Progress: 0/56 (0%)**

---

## Success Criteria

✅ **Phase 1 is complete when:**
1. All 56 items are checked off
2. Feed Service returns personalized feeds with pagination
3. Search Service returns relevant tweet results
4. All services start with `docker-compose up` without errors
5. Database migrations run successfully
6. JWT tokens have proper expiration and security
7. All health check endpoints respond with 200 OK
8. End-to-end workflow test passes (register → tweet → feed → search)

---

## Next Steps After Phase 1

Once Phase 1 is complete, you'll be ready to move to:
- **Phase 2:** Testing & CI/CD (unit tests, integration tests, GitHub Actions)
- **Phase 3:** Production Features (monitoring, rate limiting, comprehensive docs)

---

**Last Updated:** 2025-12-29
**Status:** Not Started
