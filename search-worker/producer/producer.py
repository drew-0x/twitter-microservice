import pika
import json


def setup_rabbitmq():
    """Set up RabbitMQ connection, channel, exchange and queue."""
    credentials = pika.PlainCredentials(username="server", password="pass")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", credentials=credentials)
    )
    channel = connection.channel()

    # Declare a topic exchange
    channel.exchange_declare(
        exchange="tweet_exchange", exchange_type="topic", durable=True
    )

    # Declare the queue
    channel.queue_declare(queue="tweet_events")

    # Bind the queue to the exchange with a pattern
    channel.queue_bind(
        exchange="tweet_exchange", queue="tweet_events", routing_key="tweet.#"
    )

    return connection, channel


def publish_tweet(tweet_data, action):
    """
    Publish a tweet with a specific action.

    Args:
        tweet_data: Dictionary containing tweet information
        action: String specifying the action type ("create", "update", or "delete")
    """
    connection, channel = setup_rabbitmq()

    # Use your existing routing key pattern
    routing_key = f"tweet.{action}"

    channel.basic_publish(
        exchange="tweet_exchange", routing_key=routing_key, body=json.dumps(tweet_data)
    )

    print(f" [x] Sent {tweet_data} with routing key '{routing_key}'")
    connection.close()


if __name__ == "__main__":
    # Example usage
    tweet1 = {
        "id": "test1",
        "user_id": "user123",
        "content": "This is a general tweet!",
    }
    publish_tweet(tweet1, "create")

    tweet2 = {
        "id": "test2",
        "user_id": "user123",
        "content": "This is a reply!",
    }
    publish_tweet(tweet2, "create")

    tweet3 = {
        "id": "test3",
        "user_id": "user123",
        "content": "This is a retweet!",
    }
    publish_tweet(tweet3, "create")
