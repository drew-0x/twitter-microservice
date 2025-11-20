package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"time"

	"github.com/go-redis/redis/v8"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "tweet-worker/user"

	amqp "github.com/rabbitmq/amqp091-go"
)

var ctx = context.Background()
var rdb *redis.Client

// Helper function to get an environment variable with a default value
func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

type Tweet struct {
	UserID  string `json:"user_id"`
	TweetID string `json:"tweet_id"`
}

func get_user_followers(userID string) ([]*pb.FollowStruct, error) {
	credentials := insecure.NewCredentials()
	grpcAddr := getEnv("USERS_GRPC_ADDRESS", "localhost:50051")
	conn, err := grpc.NewClient(grpcAddr, grpc.WithTransportCredentials(credentials))
	if err != nil {
		return nil, err
	}
	defer conn.Close()

	c := pb.NewUserClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	resp, err := c.GetFollowers(ctx, &pb.GetFollowersReq{UserId: userID})
	if err != nil {
		return nil, err
	}

	return resp.GetFollowers(), nil
}

func handle_message(msg amqp.Delivery) {
	var tweet Tweet

	if err := json.Unmarshal(msg.Body, &tweet); err != nil {
		log.Printf("error: %s", err)
		msg.Nack(false, true)
	}

	userID := tweet.UserID

	followers, err := get_user_followers(userID)
	if err != nil {
		log.Printf("error: %s", err)
	}

	for _, follower := range followers {
		// Push tweet to the follower's feed
		feedKey := "feed:" + follower.FollowerId
		if err := rdb.LPush(ctx, feedKey, tweet.TweetID).Err(); err != nil {
			log.Printf("Failed to push tweet to Redis for user %s: %v", follower.FollowerId, err)
			// Nack the message to requeue it for later processing
			msg.Nack(false, true)
			return
		}

		// Optional: Trim the feed to keep it at a reasonable size
		if err := rdb.LTrim(ctx, feedKey, 0, 999).Err(); err != nil {
			log.Printf("Failed to trim feed for user %s: %v", follower.FollowerId, err)
		}

		log.Printf("Tweet %s pushed to feed for user %s", tweet.TweetID, follower.FollowerId)
	}

	// Acknowledge the message after processing for all followers
	msg.Ack(false)
}

func run_worker() {
	rabbitmqURL := getEnv("RABBITMQ_URL", "amqp://server:pass@localhost:5672")
	conn, err := amqp.Dial(rabbitmqURL)
	if err != nil {
		log.Panicf("error: %s", err)
	}

	conChan, err := conn.Channel()
	if err != nil {
		log.Panicf("error: %s", err)
	}
	defer conChan.Close()

	generalTweetQueue, err := conChan.QueueDeclare(
		"general_tweets",
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Panicf("error: %s", err)
	}

	msgs, err := conChan.Consume(
		generalTweetQueue.Name,
		"",
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Panicf("error: %s", err)
	}

	var forever chan struct{}

	go func() {
		for d := range msgs {
			log.Printf("Received message %s", d.Body)
			go handle_message(d)
		}
	}()

	log.Printf("[+] Waiting for a message.")

	<-forever
}

func main() {
	redisAddr := getEnv("REDIS_ADDRESS", "localhost:6379")
	rdb = redis.NewClient(&redis.Options{
		Addr:     redisAddr, // Redis server address
		Password: "",        // No password set
		DB:       0,         // Use default DB
	})

	// Ping the Redis server to check the connection
	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Could not connect to Redis: %v", err)
	}

	run_worker()
}