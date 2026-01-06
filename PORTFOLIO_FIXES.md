# Portfolio Fixes - Remaining Tasks

This document tracks remaining fixes and improvements needed to make this project portfolio-ready. Issues are organized by priority and category.

## Completed Fixes (Previous Session)

These issues have been addressed:

- [x] JWT Secret moved to environment variable with .env fallback and warning
- [x] Token expiration implemented (48 hours)
- [x] `__table_args__` typo fixed in `users/src/models.py` and `tweets/src/models.py`
- [x] `/tweet/repose` typo fixed (now `/tweet/repost`)
- [x] `@router.route` changed to `@router.get` for getLikes
- [x] Feed service refactored with Redis integration and GET /feed endpoint
- [x] Search service refactored with mock Elasticsearch implementation
- [x] Feed service added to docker-compose.yml
- [x] GetTweets gRPC method fixed in tweets service

---

## Critical (P0) - Must Fix

### 1. Flask Route Syntax in FastAPI
**Files:** `tweets/src/routes/__init__.py`
**Issue:** Routes use Flask-style `<id>` instead of FastAPI `{id}`
**Impact:** Routes will not match correctly

```python
# Current (Flask style)
@router.get("/tweet/<id>")

# Should be (FastAPI style)
@router.get("/tweet/{id}")
```

**Lines to check:** Search for `<id>`, `<tweet_id>`, `<user_id>` patterns

---

### 2. Spelling Error in Route
**File:** `tweets/src/routes/__init__.py`
**Issue:** Route `/tweet/reposts/<id>` has inconsistent naming
**Fix:** Ensure all repost-related routes use consistent naming

---

### 3. User.query Pattern (Flask-SQLAlchemy)
**Files:** Multiple files in users and tweets services
**Issue:** Code uses `User.query.filter()` which is Flask-SQLAlchemy pattern, not pure SQLAlchemy
**Impact:** Will fail without Flask-SQLAlchemy installed

```python
# Current (Flask-SQLAlchemy)
User.query.filter(User.id == user_id).first()

# Should be (SQLAlchemy)
db_session.query(User).filter(User.id == user_id).first()
```

**Files to check:**
- `users/src/routes/__init__.py`
- `tweets/src/routes/__init__.py`
- `users/src/grpc/server/__init__.py`

---

### 4. Proto File Typo
**File:** `proto/user_service.proto`
**Issue:** `IncrementsTweets` should be `IncrementTweets` (no 's')
**Impact:** Inconsistent naming between proto and implementation

---

### 5. Search Service Mock Implementation
**File:** `search/src/dependencies/elasticsearch.py`
**Issue:** Currently returns mock data, needs real Elasticsearch integration
**Status:** Intentionally left as mock - user will implement

---

## High Priority (P1) - Should Fix

### 6. Missing gRPC Error Handling
**Files:** All gRPC client files in `*/src/grpc/client/`
**Issue:** No try/catch around gRPC calls, failures will crash the service
**Fix:** Wrap gRPC calls in try/except with proper error handling

```python
try:
    response = stub.GetUser(request)
except grpc.RpcError as e:
    logger.error(f"gRPC error: {e.code()}: {e.details()}")
    raise HTTPException(status_code=503, detail="Service unavailable")
```

---

### 7. Hardcoded gRPC Targets
**Files:**
- `feed/src/grpc/client/__init__.py`
- `tweets/src/grpc/client/__init__.py`
**Issue:** gRPC targets may be hardcoded or inconsistently configured
**Fix:** All should read from config/environment variables

---

### 8. Missing Health Check Endpoints
**Files:** `users/src/routes/__init__.py`, `tweets/src/routes/__init__.py`
**Issue:** Not all services have `/health` endpoints for container orchestration
**Fix:** Add standardized health check to all services

```python
@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "<service-name>"}
```

---

### 9. Inconsistent API Response Format
**Files:** All route files
**Issue:** Some endpoints return raw data, others wrap in response objects
**Fix:** Standardize response format across all services

```python
# Recommended format
{
    "success": true,
    "data": {...},
    "error": null
}
```

---

### 10. Missing Input Validation
**Files:** Route handlers
**Issue:** Limited use of Pydantic schemas for request validation
**Fix:** Add proper request schemas for all POST/PUT endpoints

---

## Medium Priority (P2) - Nice to Have

### 11. Logging Inconsistency
**Files:** All services
**Issue:** Mix of `print()` statements and `logging` module
**Fix:** Replace all `print()` with proper logging

---

### 12. No Database Migrations
**Issue:** Using `Base.metadata.create_all()` instead of Alembic
**Impact:** No way to track schema changes, difficult to modify production DB
**Fix:** Set up Alembic for each service with database access

---

### 13. Missing Tests
**Issue:** No unit or integration tests
**Fix:** Add pytest tests for:
- Route handlers
- gRPC services
- Database operations
- Authentication flow

---

### 14. Missing .dockerignore Files
**Files:** Each service directory
**Issue:** Docker builds may include unnecessary files
**Fix:** Add `.dockerignore` to each service:

```
__pycache__
*.pyc
.env
.venv
venv
*.egg-info
.pytest_cache
.git
```

---

### 15. Environment Variable Documentation
**Issue:** No clear documentation of required environment variables
**Fix:** Add `.env.example` file with all required variables

---

### 16. gRPC Proto Code Not Generated
**Issue:** Generated `*_pb2.py` files may be outdated or missing
**Fix:** Regenerate all proto files and ensure they're in sync

```bash
cd proto
python -m grpc_tools.protoc -I. \
  --python_out=../tweets/src/grpc/server \
  --grpc_python_out=../tweets/src/grpc/server \
  tweet_service.proto
```

---

## Low Priority (P3) - Polish

### 17. Add API Documentation
**Fix:** Configure FastAPI's automatic OpenAPI docs properly with descriptions

---

### 18. Rate Limiting
**Issue:** No rate limiting on API endpoints
**Fix:** Add slowapi or similar rate limiting middleware

---

### 19. Request ID Tracing
**Issue:** Hard to trace requests across services
**Fix:** Add request ID middleware that propagates through gRPC calls

---

### 20. Graceful Shutdown
**Issue:** Services may not shut down gracefully
**Fix:** Add signal handlers for SIGTERM/SIGINT

---

## File-by-File Checklist

### users/
- [ ] `src/routes/__init__.py` - Fix User.query pattern, add health check
- [ ] `src/grpc/server/__init__.py` - Add error handling
- [ ] `src/dependencies/auth.py` - Already fixed

### tweets/
- [ ] `src/routes/__init__.py` - Fix route syntax `<id>` to `{id}`, fix User.query
- [ ] `src/grpc/server/__init__.py` - Already fixed GetTweets
- [ ] `src/grpc/client/__init__.py` - Add error handling

### feed/
- [ ] `src/routes/__init__.py` - Already refactored
- [ ] `src/grpc/client/__init__.py` - Add error handling
- [ ] `src/dependencies/redis.py` - Already created

### search/
- [ ] `src/routes/__init__.py` - Already refactored (mock)
- [ ] `src/dependencies/elasticsearch.py` - Implement real search (user task)

### proto/
- [ ] `user_service.proto` - Fix IncrementsTweets typo
- [ ] `tweet_service.proto` - Already created
- [ ] Regenerate all Python files

### Infrastructure
- [ ] Add `.dockerignore` to all services
- [ ] Add `.env.example` with required variables
- [ ] Fix gRPC port conflicts in docker-compose.yml (Docker only)

---

## Quick Start for Fixing

1. Start with **P0 Critical** issues - these will cause runtime errors
2. Fix route syntax issues in tweets service first
3. Audit and fix User.query patterns across all files
4. Add error handling to gRPC clients
5. Add health checks to remaining services
6. Create tests as you fix each component

---

## Notes

- Search Elasticsearch implementation is intentionally left as mock
- Docker port conflicts are Docker-only issues, local dev unaffected
- JWT authentication is now properly configured with .env fallback
