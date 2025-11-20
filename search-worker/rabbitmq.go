package main

import (
	amqp "github.com/rabbitmq/amqp091-go"
)

// Helper function to get an environment variable with a default value
// This is duplicated from main.go, in a real project this would be in a shared package.

type MQClient struct {
	conn *amqp.Connection
	ch   *amqp.Channel
	q    amqp.Queue
}

func NewRabbitMQClinet() (*MQClient, error) {
	mq := &MQClient{}

	err := mq.innit()
	if err != nil {
		return nil, err
	}

	return mq, nil
}

func (mq *MQClient) innit() error {
	var err error
	// Use the service name 'rabbitmq' as the host, which is resolvable by Docker's internal DNS
	rabbitmqURL, err := getEnv("RABBITMQ_URL")
	if err != nil {
		panic("")
	}
	mq.conn, err = amqp.Dial(rabbitmqURL)
	if err != nil {
		return err
	}

	mq.ch, err = mq.conn.Channel()
	if err != nil {
		return err
	}

	// Declare the exchange
	err = mq.ch.ExchangeDeclare(
		"tweet_exchange", // exchange name
		"topic",          // exchange type
		true,             // durable
		false,            // auto-deleted
		false,            // internal
		false,            // no-wait
		nil,              // arguments
	)
	if err != nil {
		return err
	}

	// Declare the queue
	mq.q, err = mq.ch.QueueDeclare(
		"tweet_events", // queue name
		false,          // durable
		false,          // delete when unused
		false,          // exclusive
		false,          // no-wait
		nil,            // arguments
	)
	if err != nil {
		return err
	}

	// Bind the queue to the exchange with pattern
	err = mq.ch.QueueBind(
		mq.q.Name,        // queue name
		"tweet.#",        // binding key
		"tweet_exchange", // exchange
		false,            // no-wait
		nil,              // arguments
	)
	if err != nil {
		return err
	}

	return nil
}

func (mq *MQClient) Close() {
	defer mq.conn.Close()
	defer mq.ch.Close()
}

func (mq *MQClient) Consume() (<-chan amqp.Delivery, error) {
	return mq.ch.Consume(
		mq.q.Name, // queue
		"",        // consumer
		false,     // auto-ack (changed to false for manual ack)
		false,     // exclusive
		false,     // no-local
		false,     // no-wait
		nil,       // args
	)
}
