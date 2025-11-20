from typing import Dict, List
from elasticsearch import Elasticsearch
from sqlalchemy import Integer

from src.dependencies.config import config


class _ElasticsearchClient:
    def __init__(self) -> None:
        self.mappings: Dict[str, Dict] = {}
        self.es = Elasticsearch(
            hosts=config["ES_URL"], basic_auth=(config["ES_UESR"], config["ES_PASS"])
        )

        self.info = self.es.info().body

        if self.es.ping():
            print("Elasticsearch Connection Esablished!")
        else:
            raise Exception("error connecting to elasticsearch")

    def add_index(self, key: str, mapping: Dict):
        self.mappings[key] = mapping

        self.es.indices.create(index=key, mappings=mapping)

    def remove_index(self, key: str):
        self.es.indices.delete(index=key)
        del self.mappings[key]

    def create_document(self, mapping: str, id: str, data: Dict):
        if data.keys() is not self.mappings[mapping].keys():
            raise Exception("data invalid for mapping")

        self.es.index(index=mapping, id=id, document=data)

    def search_document(self, mapping: str, query: Dict[str, str | Integer]):
        """
        Query: a dict of infomration thats to be matched, e.g.
            {
                author: "John"
                content: "breaking news on us relations"
            }
        """
        response = self.es.search(
            index=mapping,
            query={
                "bool": {
                    "must": {"match_phrase": query},
                }
            },
        )

        return response

    def delete_document(self, mapping: str, id: str):
        self.es.delete(index=mapping, id=id)


esClient = _ElasticsearchClient()
