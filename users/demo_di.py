"""
Demonstration of Dependency Injection in FastAPI

This script shows how DI allows us to swap implementations easily.
"""

from fastapi import Depends, FastAPI
from typing import Generator

# ===== Example 1: Database Dependency =====

class FakeDB:
    """Mock database for demonstration"""
    def __init__(self):
        self.data = []

    def add(self, item):
        self.data.append(item)
        print(f"  [OK] Added '{item}' to FAKE database")

    def get_all(self):
        return self.data


class RealDB:
    """Real database (simulated)"""
    def add(self, item):
        print(f"  [OK] Added '{item}' to REAL database (PostgreSQL)")

    def get_all(self):
        return ["item1", "item2"]


# Dependency function - can be overridden in tests
def get_db() -> Generator[FakeDB, None, None]:
    """Provides a database session"""
    db = FakeDB()
    try:
        yield db
    finally:
        print("  [OK] Database session closed")


# Create app
app = FastAPI()


# Route uses dependency injection
@app.post("/items")
def create_item(item: str, db: FakeDB = Depends(get_db)):
    """This route gets a database automatically injected"""
    db.add(item)
    return {"message": "Item created", "items": db.get_all()}


# ===== Demonstration =====

if __name__ == "__main__":
    from fastapi.testclient import TestClient

    print("\n" + "="*60)
    print("DEMONSTRATION 1: Using Default Dependency")
    print("="*60)

    # Test with default dependency (FakeDB)
    client = TestClient(app)
    response = client.post("/items?item=apple")
    print(f"Response: {response.json()}")

    print("\n" + "="*60)
    print("DEMONSTRATION 2: Overriding Dependency for Testing")
    print("="*60)

    # Override dependency to use RealDB
    def get_real_db():
        db = RealDB()
        yield db

    app.dependency_overrides[get_db] = get_real_db

    response = client.post("/items?item=banana")
    print(f"Response: {response.json()}")

    # Clean up override
    app.dependency_overrides.clear()

    print("\n" + "="*60)
    print("KEY BENEFITS:")
    print("="*60)
    print("[+] Route code doesn't change when we swap implementations")
    print("[+] Easy to test with mock databases")
    print("[+] Automatic resource cleanup (close connections)")
    print("[+] Type hints provide IDE autocomplete")
    print("[+] Can inject multiple dependencies per route")
    print("="*60 + "\n")
