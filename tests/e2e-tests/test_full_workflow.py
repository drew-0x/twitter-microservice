

import requests
import pytest
import time
import uuid

# --- Service URLs ---
# These should match the ports in your docker-compose.yml
USERS_API_URL = "http://localhost:5000"
TWEETS_API_URL = "http://localhost:5001"
FEED_API_URL = "http://localhost:5002"
SEARCH_API_URL = "http://localhost:5003"


@pytest.fixture(scope="module")
def session_data():
    """A pytest fixture to hold data across test steps."""
    return {}


def test_full_user_workflow():
    """
    Tests a full end-to-end user workflow.
    NOTE: This test WILL FAIL until the API endpoints are implemented as per the TODO.md.
    Workflow:
    1. Register a new user.
    2. Log in with that user.
    3. Post a new tweet.
    4. Retrieve the user's feed to verify the tweet is there.
    5. Search for the tweet.
    """
    # Generate unique user credentials for this test run
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    password = "password123"

    # --- Step 1: Register a new user ---
    print(f"\n1. Registering user: {username}")
    register_response = requests.post(
        f"{USERS_API_URL}/api/users/register",
        json={"username": username, "email": email, "password": password}
    )
    # EXPECTED: This step will fail until the registration endpoint is created.
    assert register_response.status_code == 201, f"Expected 201, got {register_response.status_code}: {register_response.text}"
    print("-> User registered successfully.")

    # --- Step 2: Log in ---
    print(f"2. Logging in as user: {username}")
    login_response = requests.post(
        f"{USERS_API_URL}/api/users/login",
        json={"email": email, "password": password}
    )
    # EXPECTED: This step will fail until the login endpoint is created.
    assert login_response.status_code == 200, f"Expected 200, got {login_response.status_code}: {login_response.text}"
    access_token = login_response.json().get("access_token")
    assert access_token, "Access token not found in login response"
    print("-> Log in successful.")

    headers = {"Authorization": f"Bearer {access_token}"}

    # --- Step 3: Post a new tweet ---
    tweet_content = f"Hello world from {username}! This is a test tweet."
    print("3. Posting a new tweet.")
    tweet_response = requests.post(
        f"{TWEETS_API_URL}/api/tweets",
        json={"content": tweet_content},
        headers=headers
    )
    assert tweet_response.status_code == 201, f"Expected 201, got {tweet_response.status_code}: {tweet_response.text}"
    tweet_id = tweet_response.json().get("id")
    assert tweet_id, "Tweet ID not found in response"
    print(f"-> Tweet posted successfully (ID: {tweet_id}).")

    # --- Step 4: Check the feed ---
    # It may take a moment for the feed-worker to process the new tweet.
    print("4. Checking feed for the new tweet (waiting 5s for worker)...")
    time.sleep(5)
    feed_response = requests.get(f"{FEED_API_URL}/api/feed", headers=headers)
    assert feed_response.status_code == 200, f"Expected 200, got {feed_response.status_code}: {feed_response.text}"
    feed_data = feed_response.json()
    assert any(tweet['id'] == tweet_id for tweet in feed_data), "New tweet not found in feed"
    print("-> Tweet found in feed.")

    # --- Step 5: Search for the tweet ---
    # It may take a moment for the search-worker to index the new tweet.
    print("5. Searching for the new tweet (waiting 5s for worker)...")
    time.sleep(5)
    search_response = requests.get(f"{SEARCH_API_URL}/api/search", params={"q": tweet_content})
    assert search_response.status_code == 200, f"Expected 200, got {search_response.status_code}: {search_response.text}"
    search_results = search_response.json()
    assert any(result['_source']['content'] == tweet_content for result in search_results), "New tweet not found in search results"
    print("-> Tweet found in search results.")

    print("\n🎉 Full workflow test completed successfully! 🎉")

