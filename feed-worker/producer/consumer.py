import pika
import json


def consume_user_tweets(user_id):
    credentials = pika.PlainCredentials(username="server", password="pass")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", credentials=credentials)
    )
    channel = connection.channel()

    queue_name = f"user_feed_{user_id}"
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        tweet_data = json.loads(body)
        print(f" [x] Received {tweet_data} from {queue_name}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(f" [*] Waiting for messages from {queue_name}. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    # Example usage: Consume tweets for user ID 456
    consume_user_tweets("test")
