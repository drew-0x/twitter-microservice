import pika
import json

from src.dependencies.config import config


def produce_message(
    payload: object,
    message_queue: str,
    routing_key: str = "",
):
    RABBITMQ_USERNAME = str(config["RABBITMQ_USERNAME"])
    RABBITMQ_PASSWORD = str(config["RABBITMQ_PASSWORD"])
    RABBITMQ_HOST = str(config["RABBITMQ_HOST"])

    if not routing_key:
        routing_key = message_queue

    credentials = pika.PlainCredentials(
        username=RABBITMQ_USERNAME, password=RABBITMQ_PASSWORD
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )

    channel = connection.channel()

    channel.queue_declare(queue=message_queue)

    channel.basic_publish(
        exchange="tweet_exchange", routing_key=routing_key, body=json.dumps(payload)
    )
    print(f" [x] Sent {payload} to {message_queue}")
    connection.close()
