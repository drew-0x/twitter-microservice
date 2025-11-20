import pika
import json
import time
import random
import uuid


def load_users():
    """Loads user data from the JSON file."""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: users.json not found. Please create it.")
        return []

def publish_general_tweet(tweet_data):
    """Publishes a single tweet to the general_tweets queue."""
    credentials = pika.PlainCredentials(username="server", password="pass")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue="general_tweets")
    channel.basic_publish(
        exchange="", routing_key="general_tweets", body=json.dumps(tweet_data)
    )
    print(f" [x] Sent {tweet_data} to general_tweets")
    connection.close()


if __name__ == "__main__":
    users = load_users()
    if not users:
        exit()

    celebrities = [u for u in users if u['user_id'].startswith('celebrity_')]
    regular_users = [u for u in users if not u['user_id'].startswith('celebrity_')]

    print("Starting tweet producer... Press Ctrl+C to exit.")
    try:
        while True:
            # 95% chance for a regular user, 5% chance for a celebrity
            if random.random() < 0.05 and celebrities:
                selected_user = random.choice(celebrities)
                print(f"A celebrity is tweeting! ({selected_user['username']}) ")
            else:
                selected_user = random.choice(regular_users)

            # Create a tweet with a unique ID that matches the Go struct
            tweet = {
                "user_id": selected_user['user_id'],
                "tweet_id": str(uuid.uuid4())
            }

            publish_general_tweet(tweet)

            # Wait for a random amount of time before sending the next tweet
            sleep_time = random.uniform(0.2, 3.0)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Producer stopped.")

