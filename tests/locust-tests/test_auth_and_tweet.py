import random
from locust import HttpUser, task, between

class TwitterUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    host = "http://127.0.0.1:5000"  # Default host for user service

    def on_start(self):
        """Called when a Locust start before any task is scheduled"""
        self.client.headers = {"Content-Type": "application/json"}
        self.token = None
        self.username = f"testuser_{random.randint(1, 100000)}"
        self.password = "password123"

        # Register the user
        self.client.post("/users/register", json={
            "username": self.username,
            "password": self.password,
            "email": f"{self.username}@example.com"
        })

        # Login to get the auth token
        with self.client.post("/users/login", json={
            "email": f"{self.username}@example.com",
            "password": self.password
        }, catch_response=True) as response:
            if response.status_code == 200:
                self.token = response.json().get("token")
                self.client.headers["Authorization"] = f"Bearer {self.token}"
            else:
                response.failure(f"Failed to login, status code: {response.status_code}")

    @task
    def create_tweet(self):
        """Task to create a new tweet."""
        if not self.token:
            print("Not logged in, skipping tweet creation")
            return

        # Switch host to the tweet service for this task
        with self.client.request("POST", "http://127.0.0.1:5001/tweet", json={
            "content": f"This is a test tweet from {self.username}!"
        }, catch_response=True) as response:
            if response.status_code != 201:
                response.failure(f"Failed to create tweet, status code: {response.status_code}")
