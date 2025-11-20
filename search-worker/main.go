package main

import (
	"encoding/json"
	"log"

	amqp "github.com/rabbitmq/amqp091-go"
)

var (
	es_client *ESClient
	mq_client *MQClient
)

type Tweet struct {
	ID      string `json:"id"`
	UserID  string `json:"user_id"`
	Content string `json:"content"`
}

func handle_create(tweet Tweet) error {
	return es_client.Create(tweet)
}

func handle_update(tweet Tweet) error {
	return es_client.Update(tweet)
}

func handle_delete(tweet Tweet) error {
	return es_client.Delete(tweet.ID)
}

func handle_message(msg amqp.Delivery, ch *amqp.Channel) {
	var tweet Tweet
	if err := json.Unmarshal(msg.Body, &tweet); err != nil {
		log.Printf("error: %s", err)
		ch.Nack(msg.DeliveryTag, false, false)
		return
	}

	var err error
	switch msg.RoutingKey {
	case "tweet.create":
		err = handle_create(tweet)
	case "tweet.update":
		err = handle_update(tweet)
	case "tweet.delete":
		err = handle_delete(tweet)
	default:
		log.Printf("Unknown routing key: %s", msg.RoutingKey)
	}

	if err != nil {
		log.Printf("Error handling message: %s", err)
		ch.Nack(msg.DeliveryTag, false, true)
	} else {
		ch.Ack(msg.DeliveryTag, false)
	}
}

func run_worker() {
	var err error
	es_client, err = NewClient()
	if err != nil {
		panic(err)
	}

	mq_client, err = NewRabbitMQClinet()
	if err != nil {
		panic(err)
	}
	defer mq_client.Close()

	msgs, err := mq_client.Consume()
	if err != nil {
	}

	var forever chan struct{}
	go func() {
		for d := range msgs {
			log.Printf("Received message %s", d.Body)
			handle_message(d, mq_client.ch)
		}
	}()

	log.Printf("[+] Waiting for a message.")
	<-forever
}

func main() {
	run_worker()
}
