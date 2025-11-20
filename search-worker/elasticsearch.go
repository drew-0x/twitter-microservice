package main

import (
	"bytes"
	"encoding/json"
	"log"

	"github.com/elastic/go-elasticsearch/v9"
)

type ESClient struct {
	es    *elasticsearch.Client
	index string
}

func NewClient() (*ESClient, error) {
	client := &ESClient{}
	elasticURL, err := getEnv("ELASTICSEARCH_URL")
	if err != nil {
		panic(err)
	}
	cfg := elasticsearch.Config{
		Addresses: []string{
			elasticURL,
		},
	}
	client.es, err = elasticsearch.NewClient(cfg)
	if err != nil {
		return nil, err
	}
	client.es.Indices.Create("tweets")

	return client, nil
}

func (c *ESClient) Create(t Tweet) error {
	data, err := json.Marshal(t)
	if err != nil {
		return err
	}
	log.Println(c.es.Index("tweets", bytes.NewReader(data)))
	return nil
}

func (c *ESClient) Update(t Tweet) error {
	var err error

	err = c.Delete(t.ID)
	if err != nil {
		return err
	}

	err = c.Create(t)
	if err != nil {
		return err
	}

	return nil
}

func (c *ESClient) Delete(id string) error {
	_, err := c.es.Delete("tweets", id)
	if err != nil {
		return err
	}
	return nil
}
