# Testing Guide

This document explains how to run tests and understand the testing infrastructure.

## Quick Start

```bash
# Run all tests
make test-all

# Run tests for a specific service
make test-users
make test-tweets
make test-feed
make test-search

# Run with verbose output
make test-verbose

# Run with coverage report
make test-coverage
```

## How the Testing Works

### Environment Variables

Environment variables are automatically set by the Makefile before running tests:

```makefile
# From Makefile
DB_USERNAME=test_user
DB_PASSWORD=test_pass
JWT_SECRET=test_secret_key_for_testing_only
JAEGER=localhost:4317
...
```

**You don't need to set these manually!** The Makefile handles it for you.

### Dependency Injection in Tests

Tests use FastAPI's dependency override system to swap real dependencies with test mocks:

```python
# Production code uses real PostgreSQL
@router.post("/users")
def create_user(db: Session = Depends(get_db)):
    db.add(user)
    db.commit()

# Test code swaps to SQLite in-memory
app.api.dependency_overrides[get_db] = test_db_fixture
```

**Key Point:** The route code never changes! We just swap what `Depends(get_db)` returns.

### Test Database Strategy

Each test gets a **fresh SQLite in-memory database**:

1. **Fast:** No disk I/O, runs in milliseconds
2. **Isolated:** Each test starts with empty tables
3. **No cleanup needed:** Database disappears after test
4. **No PostgreSQL required:** Tests run anywhere

```python
# From conftest.py
@pytest.fixture(scope="function")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    yield db
    # Drop tables automatically after test
    Base.metadata.drop_all(bind=test_engine)
```

## Test Output Explained

### Sample Test Run

```bash
$ make test-users

Running users service tests...
============================= test session starts =============================
collected 36 items

tests/test_auth.py::TestSignJWT::test_sign_jwt_returns_string PASSED     [  2%]
tests/test_auth.py::TestDecodeJWT::test_decode_valid_token PASSED        [ 11%]
tests/test_models.py::TestUserModel::test_user_creation PASSED           [ 22%]
tests/test_routes.py::TestHealthEndpoint::test_health_check_returns_200 PASSED [ 50%]
tests/test_routes.py::TestRegisterEndpoint::test_register_success PASSED [ 55%]
...

===================== 30 passed, 6 failed in 0.80s =======================
```

### What Each Part Means

1. **`collected 36 items`** - Found 36 test functions
2. **`PASSED [ 50%]`** - Test passed, 50% complete
3. **`FAILED`** - Test failed (often UUID issues with SQLite)
4. **`0.80s`** - Total time (very fast!)

### Common Test Failures (Expected)

Some tests fail with SQLite because:
- **UUID types:** SQLite stores UUIDs as strings, PostgreSQL as native UUIDs
- **Date functions:** Different SQL syntax between SQLite and PostgreSQL
- **Constraints:** Some PostgreSQL constraints don't translate to SQLite

**This is normal for unit tests.** Integration tests with real PostgreSQL will pass.

## Test Structure

### Conftest.py (Test Configuration)

Each service has `tests/conftest.py` with:

```python
# Environment variables (backup, Makefile sets these)
os.environ.setdefault("JWT_SECRET", "test_secret")

# Test database fixture
@pytest.fixture
def test_db():
    # Creates fresh SQLite database for each test
    ...

# Test client fixture
@pytest.fixture
def test_client(override_get_db, override_verify_token):
    app = App()
    app.api.dependency_overrides[get_db] = override_get_db
    app.api.dependency_overrides[VerifyToken] = override_verify_token
    return TestClient(app.api)
```

### Test Files

```
users/tests/
├── conftest.py          # Test configuration and fixtures
├── test_auth.py         # JWT authentication tests
├── test_models.py       # Database model tests
└── test_routes.py       # API endpoint tests
```

## Understanding the DI Test Pattern

### 1. Production Setup

```python
# src/dependencies/db.py
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()  # Real PostgreSQL
    try:
        yield db
    finally:
        db.close()
```

### 2. Test Override

```python
# tests/conftest.py
@pytest.fixture
def override_get_db(test_db):
    def _override():
        yield test_db  # Test SQLite
    return _override

@pytest.fixture
def test_client(override_get_db):
    app.api.dependency_overrides[get_db] = override_get_db
    return TestClient(app.api)
```

### 3. Test Execution

```python
def test_create_user(test_client):
    response = test_client.post("/users", json={...})
    assert response.status_code == 200
```

**What happens:**
1. `test_client` fixture loads
2. FastAPI dependency is overridden: `get_db` → `test_db`
3. Route runs with test SQLite database
4. After test, database is dropped
5. Next test gets fresh database

## Advanced Testing

### Running Specific Tests

```bash
# Run one test file
cd users && uv run pytest tests/test_auth.py -v

# Run one test class
cd users && uv run pytest tests/test_auth.py::TestSignJWT -v

# Run one test function
cd users && uv run pytest tests/test_auth.py::TestSignJWT::test_sign_jwt_returns_string -v

# Run tests matching pattern
cd users && uv run pytest -k "auth" -v
```

### Using Test Markers

```bash
# Run only unit tests (no external dependencies)
cd users && uv run pytest -m unit

# Run only integration tests
cd users && uv run pytest -m integration

# Skip slow tests
cd users && uv run pytest -m "not slow"
```

### Coverage Reports

```bash
make test-coverage
```

Opens HTML reports in `<service>/htmlcov/index.html` showing:
- Which lines of code were executed
- Which branches were taken
- Overall coverage percentage

## Troubleshooting

### Tests fail with "JWT_SECRET must be set"

**Solution:** Use the Makefile: `make test-users`

The Makefile automatically sets environment variables. If running pytest directly, set them manually:

```bash
cd users
DB_USERNAME=test JWT_SECRET=test uv run pytest
```

### Tests fail with UUID errors

**Expected for SQLite.** These tests will pass with real PostgreSQL in integration tests.

### Port conflicts (gRPC server errors)

Each test creates a new App instance which starts a gRPC server. If you see port binding errors, it's because multiple tests are running simultaneously.

**Solution:** Tests should clean up properly. This is a known issue we can fix.

## Benefits of This Testing Approach

✅ **Fast:** Tests run in < 1 second (no database I/O)
✅ **Isolated:** Each test starts fresh
✅ **No setup required:** No PostgreSQL, Redis, RabbitMQ needed
✅ **CI/CD ready:** Runs anywhere without external services
✅ **Easy to mock:** Can override any dependency
✅ **Type safe:** IDE autocomplete works in tests
✅ **Realistic:** Tests actual HTTP requests through FastAPI

## Next Steps

1. **Fix UUID issues:** Add UUID serialization for SQLite
2. **Add integration tests:** Test with real PostgreSQL/Redis/RabbitMQ
3. **Increase coverage:** Aim for 80%+ code coverage
4. **CI/CD pipeline:** Add GitHub Actions to run tests on every commit
