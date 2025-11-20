package main

import (
	"errors"
	"os"
)

func getEnv(key string) (string, error) {
	if value, ok := os.LookupEnv(key); ok {
		return value, nil
	}
	return "", errors.New("invalid key")
}
