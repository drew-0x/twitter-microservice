package main

//
// import (
// 	"encoding/json"
// 	"testing"
// 	"time"
//
// 	amqp "github.com/rabbitmq/amqp091-go"
// 	"github.com/stretchr/testify/assert"
// 	"github.com/stretchr/testify/mock"
// )
//
// // MockESClient is a mock implementation of the ESClient
// type MockESClient struct {
// 	mock.Mock
// }
//
// func (m *MockESClient) Create(t Tweet) error {
// 	args := m.Called(t)
// 	return args.Error(0)
// }
//
// func (m *MockESClient) Update(t Tweet) error {
// 	args := m.Called(t)
// 	return args.Error(0)
// }
//
// func (m *MockESClient) Delete(id string) error {
// 	args := m.Called(id)
// 	return args.Error(0)
// }
//
// // MockChannel is a mock implementation of amqp.Channel
// type MockChannel struct {
// 	mock.Mock
// }
//
// func (m *MockChannel) Ack(tag uint64, multiple bool) error {
// 	args := m.Called(tag, multiple)
// 	return args.Error(0)
// }
//
// func (m *MockChannel) Nack(tag uint64, multiple bool, requeue bool) error {
// 	args := m.Called(tag, multiple, requeue)
// 	return args.Error(0)
// }
//
// func TestHandleMessage_Create(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	testTweet := Tweet{
// 		ID:      "123",
// 		UserID:  "user1",
// 		Content: "Hello world",
// 	}
// 	tweetBytes, _ := json.Marshal(testTweet)
//
// 	msg := amqp.Delivery{
// 		Body:        tweetBytes,
// 		RoutingKey:  "tweet.create",
// 		DeliveryTag: 1,
// 	}
//
// 	mockES.On("Create", testTweet).Return(nil).Once()
// 	mockChannel.On("Ack", msg.DeliveryTag, false).Return(nil).Once()
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertExpectations(t)
// 	mockChannel.AssertExpectations(t)
// }
//
// func TestHandleMessage_Update(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	testTweet := Tweet{
// 		ID:      "123",
// 		UserID:  "user1",
// 		Content: "Updated content",
// 	}
// 	tweetBytes, _ := json.Marshal(testTweet)
//
// 	msg := amqp.Delivery{
// 		Body:        tweetBytes,
// 		RoutingKey:  "tweet.update",
// 		DeliveryTag: 1,
// 	}
//
// 	mockES.On("Update", testTweet).Return(nil).Once()
// 	mockChannel.On("Ack", msg.DeliveryTag, false).Return(nil).Once()
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertExpectations(t)
// 	mockChannel.AssertExpectations(t)
// }
//
// func TestHandleMessage_Delete(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	testTweet := Tweet{
// 		ID:      "123",
// 		UserID:  "user1",
// 		Content: "Content to be deleted",
// 	}
// 	tweetBytes, _ := json.Marshal(testTweet)
//
// 	msg := amqp.Delivery{
// 		Body:        tweetBytes,
// 		RoutingKey:  "tweet.delete",
// 		DeliveryTag: 1,
// 	}
//
// 	mockES.On("Delete", testTweet.ID).Return(nil).Once()
// 	mockChannel.On("Ack", msg.DeliveryTag, false).Return(nil).Once()
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertExpectations(t)
// 	mockChannel.AssertExpectations(t)
// }
//
// func TestHandleMessage_InvalidJson(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	msg := amqp.Delivery{
// 		Body:        []byte("invalid json"),
// 		RoutingKey:  "tweet.create",
// 		DeliveryTag: 1,
// 	}
//
// 	mockChannel.On("Nack", msg.DeliveryTag, false, true).Return(nil).Once()
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertNotCalled(t, "Create")
// 	mockES.AssertNotCalled(t, "Update")
// 	mockES.AssertNotCalled(t, "Delete")
// 	mockChannel.AssertExpectations(t)
// }
//
// func TestHandleMessage_UnknownRoutingKey(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	testTweet := Tweet{
// 		ID:      "123",
// 		UserID:  "user1",
// 		Content: "Hello world",
// 	}
// 	tweetBytes, _ := json.Marshal(testTweet)
//
// 	msg := amqp.Delivery{
// 		Body:        tweetBytes,
// 		RoutingKey:  "unknown.key",
// 		DeliveryTag: 1,
// 	}
//
// 	mockChannel.On("Ack", msg.DeliveryTag, false).Return(nil).Once() // Should still ack unknown keys
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertNotCalled(t, "Create")
// 	mockES.AssertNotCalled(t, "Update")
// 	mockES.AssertNotCalled(t, "Delete")
// 	mockChannel.AssertExpectations(t)
// }
//
// func TestHandleMessage_ESClientError(t *testing.T) {
// 	mockES := new(MockESClient)
// 	mockChannel := new(MockChannel)
// 	es_client = mockES // Set the global es_client to our mock
//
// 	testTweet := Tweet{
// 		ID:      "123",
// 		UserID:  "user1",
// 		Content: "Hello world",
// 	}
// 	tweetBytes, _ := json.Marshal(testTweet)
//
// 	msg := amqp.Delivery{
// 		Body:        tweetBytes,
// 		RoutingKey:  "tweet.create",
// 		DeliveryTag: 1,
// 	}
//
// 	mockES.On("Create", testTweet).Return(assert.AnError).Once()
// 	mockChannel.On("Nack", msg.DeliveryTag, false, true).Return(nil).Once()
//
// 	handle_message(msg, mockChannel)
//
// 	mockES.AssertExpectations(t)
// 	mockChannel.AssertExpectations(t)
// }
