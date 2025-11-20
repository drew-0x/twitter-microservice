package main

import (
	"encoding/json"
	"errors"
	"testing"

	amqp "github.com/rabbitmq/amqp091-go"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	pb "tweet-worker/user"
)

// MockUserClient is a mock implementation of the User gRPC client
type MockUserClient struct {
	mock.Mock
}

func (m *MockUserClient) GetFollowers(ctx context.Context, in *pb.GetFollowersReq, opts ...grpc.CallOption) (*pb.GetFollowersRes, error) {
	args := m.Called(ctx, in)
	return args.Get(0).(*pb.GetFollowersRes), args.Error(1)
}

// MockRedisClient is a mock implementation of the Redis client
type MockRedisClient struct {
	mock.Mock
}

func (m *MockRedisClient) LPush(ctx context.Context, key string, values ...interface{}) *redis.IntCmd {
	args := m.Called(ctx, key, values)
	return args.Get(0).(*redis.IntCmd)
}

func (m *MockRedisClient) LTrim(ctx context.Context, key string, start, stop int64) *redis.StatusCmd {
	args := m.Called(ctx, key, start, stop)
	return args.Get(0).(*redis.StatusCmd)
}

// MockChannel is a mock implementation of amqp.Channel
type MockChannel struct {
	mock.Mock
}

func (m *MockChannel) Ack(tag uint64, multiple bool) error {
	args := m.Called(tag, multiple)
	return args.Error(0)
}

func (m *MockChannel) Nack(tag uint64, multiple bool, requeue bool) error {
	args := m.Called(tag, multiple, requeue)
	return args.Error(0)
}

func TestHandleMessage_Success(t *testing.T) {
	mockUserClient := new(MockUserClient)
	mockRedis := new(MockRedisClient)
	mockChannel := new(MockChannel)

	// Override global variables for testing
	rdb = mockRedis

	testTweet := Tweet{
		UserID:  "author1",
		TweetID: "tweet123",
	}
	tweetBytes, _ := json.Marshal(testTweet)

	msg := amqp.Delivery{
		Body:        tweetBytes,
		DeliveryTag: 1,
	}

	// Mock GetFollowers response
	mockUserClient.On("GetFollowers", mock.Anything, &pb.GetFollowersReq{UserId: "author1"}).Return(
		&pb.GetFollowersRes{
			Followers: []*pb.FollowStruct{
				{FollowerId: "follower1"},
				{FollowerId: "follower2"},
			},
		},
		nil,
	).Once()

	// Mock Redis LPush and LTrim for each follower
	for _, followerID := range []string{"follower1", "follower2"} {
		mockRedis.On("LPush", mock.Anything, "feed:"+followerID, []interface{}{testTweet.TweetID}).Return(redis.NewIntCmd(0, nil)).Once()
		mockRedis.On("LTrim", mock.Anything, "feed:"+followerID, int64(0), int64(999)).Return(redis.NewStatusCmd(nil)).Once()
	}

	// Mock message acknowledgment
	mockChannel.On("Ack", msg.DeliveryTag, false).Return(nil).Once()

	// Call the function under test
	handle_message(msg, mockChannel)

	// Assert expectations
	mockUserClient.AssertExpectations(t)
	mockRedis.AssertExpectations(t)
	mockChannel.AssertExpectations(t)
}

func TestHandleMessage_InvalidJson(t *testing.T) {
	mockChannel := new(MockChannel)

	msg := amqp.Delivery{
		Body:        []byte("invalid json"),
		DeliveryTag: 1,
	}

	mockChannel.On("Nack", msg.DeliveryTag, false, true).Return(nil).Once()

	handle_message(msg, mockChannel)

	mockChannel.AssertExpectations(t)
}

func TestHandleMessage_GetFollowersError(t *testing.T) {
	mockUserClient := new(MockUserClient)
	mockChannel := new(MockChannel)

	// Override global variables for testing
	rdb = new(MockRedisClient) // Ensure Redis is mocked even if not called

	testTweet := Tweet{
		UserID:  "author1",
		TweetID: "tweet123",
	}
	tweetBytes, _ := json.Marshal(testTweet)

	msg := amqp.Delivery{
		Body:        tweetBytes,
		DeliveryTag: 1,
	}

	mockUserClient.On("GetFollowers", mock.Anything, &pb.GetFollowersReq{UserId: "author1"}).Return(
		&pb.GetFollowersRes{}, errors.New("gRPC error"),
	).Once()

	mockChannel.On("Nack", msg.DeliveryTag, false, true).Return(nil).Once()

	handle_message(msg, mockChannel)

	mockUserClient.AssertExpectations(t)
	mockChannel.AssertExpectations(t)
}

func TestHandleMessage_RedisLPushError(t *testing.T) {
	mockUserClient := new(MockUserClient)
	mockRedis := new(MockRedisClient)
	mockChannel := new(MockChannel)

	// Override global variables for testing
	rdb = mockRedis

	testTweet := Tweet{
		UserID:  "author1",
		TweetID: "tweet123",
	}
	tweetBytes, _ := json.Marshal(testTweet)

	msg := amqp.Delivery{
		Body:        tweetBytes,
		DeliveryTag: 1,
	}

	mockUserClient.On("GetFollowers", mock.Anything, &pb.GetFollowersReq{UserId: "author1"}).Return(
		&pb.GetFollowersRes{
			Followers: []*pb.FollowStruct{
				{FollowerId: "follower1"},
			},
		},
		nil,
	).Once()

	mockRedis.On("LPush", mock.Anything, "feed:follower1", []interface{}{testTweet.TweetID}).Return(redis.NewIntCmd(0, errors.New("Redis error"))).Once()

	mockChannel.On("Nack", msg.DeliveryTag, false, true).Return(nil).Once()

	handle_message(msg, mockChannel)

	mockUserClient.AssertExpectations(t)
	mockRedis.AssertExpectations(t)
	mockChannel.AssertExpectations(t)
}
