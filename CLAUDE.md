# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Twitter-like microservices backend implementing user management, tweets, personalized feeds, and search functionality. The system uses a microservices architecture with synchronous gRPC communication, asynchronous RabbitMQ messaging, and a fan-out-on-write feed generation strategy.

## Architecture

### Communication Patterns

**Service-to-Service Communication:**
- **gRPC**: Synchronous inter-service calls (User ↔ Tweet, Feed → Tweet, Tweet → User)
- **RabbitMQ**: Asynchronous event-driven messaging for feed fan-out and search indexing
- **REST/HTTP**: Client-facing APIs on all services

**Key Architectural Pattern - Feed Fan-Out:**
1. Tweet service publishes new tweet to `general_tweets` queue (RabbitMQ)
2. Feed worker consumes message, calls User service gRPC to get followers
3. Feed worker pushes tweet ID to each follower's Redis list (`feed:{user_id}`)
4. Feed service reads from Redis, hydrates tweet data via Tweet service gRPC

**Search Indexing Flow:**
1. Tweet service publishes to `tweet_events` exchange with routing key `tweet.create`
2. Search worker consumes messages and indexes tweets to Elasticsearch
3. Search service queries Elasticsearch for full-text search

### Service Responsibilities

**users/** - User Service (FastAPI + gRPC server on :50051)
- Authentication (JWT generation/verification)
- User registration, login, profiles
- Follow/unfollow relationships
- Exposes gRPC: `GetUser`, `IncrementsTweets`, `GetFollowers`, `GetFollowing`

**tweets/** - Tweet Service (FastAPI + gRPC server on :50051)
- Tweet CRUD, replies, likes, reposts
- Publishes to RabbitMQ queues: `general_tweets`, `tweet_events`
- Calls User service gRPC to increment tweet counts
- Should expose gRPC: `GetTweets` (for feed hydration - currently missing)

**feed/** - Feed Service (FastAPI)
- Serves personalized user feeds (`GET /feed`)
- Reads tweet IDs from Redis lists
- Hydrates full tweet data via Tweet service gRPC
- Currently incomplete - endpoint exists but needs implementation

**search/** - Search Service (FastAPI)
- Elasticsearch-based tweet search
- Currently incomplete - needs search endpoint implementation

**feed-worker/** - Feed Worker (Go)
- Consumes `general_tweets` queue
- Fan-out pattern: pushes tweet IDs to Redis lists for each follower
- Uses gRPC to call User service `GetFollowers`
- Redis key pattern: `feed:{follower_id}`

**search-worker/** - Search Worker (Go)
- Consumes `tweet_events` exchange (routing key: `tweet.create`)
- Indexes tweets to Elasticsearch
- Handles `tweet.create`, `tweet.update`, `tweet.delete` routing keys

### Data Stores

**PostgreSQL** (shared by users + tweets services):
- Users service: `actors` table, `follows` table
- Tweets service: `tweets`, `reply_tweets`, `tweet_like`, `tweet_repost` tables
- **Important**: Each service owns its schema but uses same Postgres instance (anti-pattern noted in docs)

**Redis**:
- Feed data storage with keys: `feed:{user_id}`
- Lists store tweet IDs (newest first via LPUSH)
- Feed worker trims to 1000 tweets max (LTRIM 0 999)

**Elasticsearch**:
- Tweet index for full-text search
- Populated by search-worker

## Development Commands

### Environment Setup

**Install dependencies for a service:**
```bash
cd <service-name>  # users, tweets, feed, or search
uv sync
```

**Start infrastructure only:**
```bash
docker-compose up postgres redis rabbitmq elasticsearch jaeger -d
```

**Start all services:**
```bash
docker-compose up --build
```

### Running Services Locally

**Python services (users, tweets, feed, search):**
```bash
cd <service-name>
python main.py
# Runs FastAPI on :5000 (configurable via .env)
# gRPC server starts on :50051 in separate thread
```

**Go workers (feed-worker, search-worker):**
```bash
cd <service-name>
go run .
```

### Code Quality

**Format Python code:**
```bash
cd <service-name>
black src/
```

**Lint Python code:**
```bash
cd <service-name>
ruff check src/
```

**Run tests:**
```bash
cd <service-name>
pytest
```

**Go tests:**
```bash
cd <service-name>
go test -v
```

### gRPC Protocol Buffers

**Location:** `proto/` directory contains `.proto` files

**Regenerate Python gRPC code:**
```bash
cd proto
python -m grpc_tools.protoc -I. \
  --python_out=../<service>/src/grpc/<client|server> \
  --grpc_python_out=../<service>/src/grpc/<client|server> \
  <proto-file>.proto
```

Example for user service:
```bash
cd proto
python -m grpc_tools.protoc -I. \
  --python_out=../users/src/grpc \
  --grpc_python_out=../users/src/grpc \
  user_service.proto
```

## Project Structure Patterns

### Python Services (users, tweets, feed, search)

```
<service>/
├── main.py                    # Entry point, starts FastAPI + gRPC server
├── src/
│   ├── __init__.py           # App class, FastAPI setup, OpenTelemetry
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic request/response models
│   ├── routes/               # FastAPI route handlers
│   │   └── __init__.py or *_routes.py
│   ├── dependencies/
│   │   ├── auth.py          # JWT sign/decode, VerifyToken dependency
│   │   ├── config.py        # Config class (reads config.toml + .env)
│   │   ├── db.py            # SQLAlchemy setup, init_db()
│   │   └── mq.py            # RabbitMQ produce_message()
│   └── grpc/
│       ├── server.py        # gRPC servicer implementation
│       └── client/          # Generated *_pb2.py files for calling other services
```

### Key Implementation Details

**FastAPI + gRPC Dual Server:**
- Each Python service runs FastAPI (port 5000) and gRPC server (port 50051) concurrently
- gRPC server starts in daemon thread via `src/__init__.py` App class
- See `users/src/__init__.py` for pattern

**Authentication Flow:**
- `users/src/dependencies/auth.py`: `sign_jwt()` creates tokens, `VerifyToken` is FastAPI dependency
- JWT payload: `{"user_id": str, "username": str, "exp": timestamp, "iat": timestamp}`
- All authenticated endpoints use `user: UserToken = Depends(VerifyToken)`

**Database Models:**
- All models have `to_dict()` method for serialization
- User model has `verify_password()` and `increment_followers()`, `increment_tweets()`
- Tweet models have `increment_likes()`, `decrement_likes()`, etc.
- Note: Some models have typo `__tabel_args__` instead of `__table_args__` (doesn't apply constraints!)

**Configuration:**
- Root `config.toml` + `.env` define all settings
- Each service reads via `src/dependencies/config.py` Config class
- Config uses TOML sections: `[Database]`, `[JWT]`, `[UserService]`, etc.

**RabbitMQ Message Format:**
- Tweet message: `{"user_id": "uuid", "tweet_id": "uuid", "content": "...", ...}`
- Published to queues: `general_tweets` (for feed), `tweet_events` exchange (for search)
- Routing keys: `tweet.create`, `tweet.update`, `tweet.delete`

## Known Issues & Implementation Gaps

> **See `PORTFOLIO_FIXES.md` for the complete, prioritized list of remaining fixes.**

### Recently Fixed (January 2026)
- [x] JWT Secret moved to environment variable with .env fallback
- [x] Token expiration implemented (48 hours)
- [x] `__table_args__` typo fixed in models
- [x] `/tweet/repose` typo fixed
- [x] `@router.route` changed to `@router.get`
- [x] Feed service refactored with Redis + gRPC
- [x] Search service refactored with mock Elasticsearch
- [x] GetTweets gRPC method implemented

### Remaining Critical Issues (P0)
1. **Flask route syntax in FastAPI** - `tweets/src/routes/__init__.py` uses `<id>` instead of `{id}`
2. **User.query pattern** - Flask-SQLAlchemy pattern used instead of pure SQLAlchemy
3. **Proto typo** - `IncrementsTweets` should be `IncrementTweets`

### Remaining High Priority (P1)
- Missing gRPC error handling in client files
- Hardcoded gRPC targets need config
- Missing health check endpoints on some services
- Inconsistent API response format

### Still Missing
- Real Elasticsearch implementation (intentionally mocked)
- Database migrations (using `create_all()`)
- Unit/integration tests
- `.dockerignore` files

**Port Conflicts (Docker only):**
- docker-compose.yml has gRPC port conflicts (multiple services on :50051)
- Users should be :50051, Tweets :50052, Search :50053

## Testing & Validation

**Manual Testing Flow:**
1. Register user: `POST /register` on users service
2. Login: `POST /login` → get JWT token
3. Create tweet: `POST /tweet` with JWT on tweets service
4. Check RabbitMQ: message in `general_tweets` queue
5. Feed worker processes → check Redis: `redis-cli LRANGE feed:{user_id} 0 -1`
6. Get feed: `GET /feed` with JWT on feed service

**Monitoring:**
- Jaeger UI: http://localhost:16686 (distributed tracing)
- RabbitMQ Management: http://localhost:15672 (user: server, pass: pass)
- Elasticsearch: http://localhost:9200

## Database Schema Notes

**Users Service:**
- `actors` table: Users with unique email/username constraints
- `follows` table: Many-to-many follower relationships with UniqueConstraint

**Tweets Service:**
- `tweets` table: Main tweets
- `reply_tweets`: Replies with parent_id reference
- `tweet_like`, `tweet_repost`: Junction tables with UniqueConstraints to prevent duplicates

**Indexes:**
- Models define composite indexes for common queries (user_id + created_at)
- See `users/src/models.py` and `tweets/src/models.py` for `__table_args__` patterns

## Important Implementation Notes

**When adding new gRPC methods:**
1. Update `.proto` file in `proto/` directory
2. Regenerate Python code for both client and server
3. Implement servicer method in `src/grpc/server.py`
4. Import and use in client service from `src/grpc/client/*_pb2.py`

**When adding new RabbitMQ consumers:**
- Queue name and routing key must match producer exactly
- Use `msg.Ack(false)` on success, `msg.Nack(false, true)` to requeue on failure
- See `feed-worker/main.go` and `search-worker/main.go` for patterns

**When modifying database models:**
- Add indexes for foreign keys and frequently queried columns
- Use UniqueConstraint for junction tables to prevent duplicates
- Spell `__table_args__` correctly (not `__tabel_args__`)!
- Eventually: Create Alembic migration instead of relying on `create_all()`

**OpenTelemetry Instrumentation:**
- All services auto-instrument FastAPI, gRPC, and requests
- Traces sent to Jaeger (configured in `src/__init__.py` App class)
- Service names: "user-service", "tweet-service", etc.

## Notion Documentation & Task Management

**Important:** This project has comprehensive internal documentation in Notion. Always check Notion for the latest task status, architecture details, and known issues before making changes.

### Notion Structure

**Main Hub Page:**
- **Twitter Microservices - Portfolio Project** (ID: `2defbee07341811298a9de44736b6258`)
- Clean landing page with links to all documentation and databases
- URL: https://www.notion.so/2defbee07341811298a9de44736b6258

**Core Documentation Pages:**
1. **🏗️ Architecture & Design** (ID: `2defbee07341812ea074df05a97dd5b6`)
   - Complete system architecture
   - Service topology and responsibilities
   - Communication patterns (gRPC, RabbitMQ, REST)
   - Data architecture (PostgreSQL, Redis, Elasticsearch)
   - Fan-out-on-write pattern details
   - Design decisions and trade-offs

2. **🔧 Setup & Development** (ID: `2defbee07341812ea9f6cc47c7734b92`)
   - Environment setup instructions
   - Development commands
   - Testing procedures
   - Database access commands
   - Troubleshooting guide

3. **🔴 Known Issues & Bugs** (ID: `2defbee0734181cbbab9e49ed12ec1be`)
   - **CRITICAL:** Check this page before starting any work!
   - Security vulnerabilities (P0 priority)
   - High priority bugs
   - Missing implementations
   - Infrastructure issues
   - Priority matrix with effort estimates

4. **📅 Implementation Roadmap** (ID: `2defbee0734181dab613cb1f493e9ac8`)
   - Week-by-week implementation plan
   - Task breakdown with time estimates
   - Milestone checklists
   - Dependency graph

5. **🔍 Monitoring & Debugging** (ID: `2defbee0734181a6ad8bd26db345408c`)
   - Infrastructure UIs and access
   - CLI debugging commands
   - Common debugging scenarios
   - Performance monitoring tips

**Databases:**

1. **📋 Implementation Tasks** (Kanban Board)
   - **Purpose:** Track all implementation tasks
   - **Properties:**
     - **Task** (title): Task name
     - **Status** (status): To Do, In Progress, Done, Blocked
     - **Priority** (select): P0-Critical, P1-High, P2-Medium, P3-Low
     - **Category** (select): 🔒Security, 🐛Bug Fix, ✨Feature, 🏗️Infrastructure, 🧪Testing, 📖Documentation
     - **Effort** (select): XS (<1h), S (1-2h), M (3-5h), L (6-10h), XL (10h+)
     - **Week** (select): Week 1, Week 2
     - **Files** (text): Affected file paths
   - **View:** Board grouped by Status (for Kanban workflow)

2. **Services Registry**
   - **Purpose:** Catalog all services and workers
   - Contains: Users Service, Tweets Service, Feed Service, Search Service, Feed Worker, Search Worker
   - Each entry includes: Description, technology, ports, dependencies, status

### When to Use Notion

**Before Starting Any Task:**
1. Check **Known Issues & Bugs** page for existing problems
2. Review **Implementation Tasks** Kanban for task status
3. Consult **Architecture & Design** for system understanding

**When Making Changes:**
1. Update task status in Kanban (To Do → In Progress → Done)
2. Add new bugs/issues to **Known Issues & Bugs** page if discovered
3. Update **Services Registry** if adding new services

**After Completing Work:**
1. Mark tasks as Done in Kanban
2. Update documentation if architecture changed
3. Remove fixed issues from **Known Issues & Bugs**

### Using Notion MCP Tools

**Available MCP tools for Notion:**
- `mcp__notion__notion-search`: Search across workspace
- `mcp__notion__notion-fetch`: Get page/database content
- `mcp__notion__notion-create-pages`: Create new pages
- `mcp__notion__notion-update-page`: Update existing pages
- `mcp__notion__notion-update-database`: Modify database schema
- `mcp__notion__notion-create-database`: Create new databases

**Example Workflow:**
```
# Check current tasks
notion-search(query="critical security", query_type="internal")

# Get latest known issues
notion-fetch(id="2defbee0734181cbbab9e49ed12ec1be")

# Update task status
notion-update-page(page_id="<task-id>", properties={"Status": "Done"})
```

### Critical Security Issues (Always Check First!)

**FIXED P0 Issues (January 2026):**
1. ~~**JWT Secret Hardcoded**~~ - Now reads from `JWT_SECRET` env var with .env fallback + warning
2. ~~**No Token Expiration**~~ - JWT tokens now expire in 48 hours (`exp` field added)
3. ~~**Database Constraints Not Enforced**~~ - `__table_args__` typo fixed in all models

**Remaining P0 Issues:**
- Flask route syntax `<id>` in FastAPI (tweets service)
- `User.query` pattern needs SQLAlchemy `db_session.query()` pattern
- See `PORTFOLIO_FIXES.md` for complete list

### Task Priorities

**P0 (Critical):** Must fix before deployment - security vulnerabilities
**P1 (High):** Breaks functionality or blocks other work
**P2 (Medium):** Core features needed for portfolio
**P3 (Low):** Nice-to-have, polish, testing

### Notion Page IDs Reference

Keep these IDs for quick access:
- Main Hub: `2defbee07341811298a9de44736b6258`
- Architecture: `2defbee07341812ea074df05a97dd5b6`
- Setup: `2defbee07341812ea9f6cc47c7734b92`
- Known Issues: `2defbee0734181cbbab9e49ed12ec1be`
- Roadmap: `2defbee0734181dab613cb1f493e9ac8`
- Monitoring: `2defbee0734181a6ad8bd26db345408c`
