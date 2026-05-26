import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from app.config import settings


class ChromaClient:
    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None):
        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata or {"description": f"Collection for {name}"}
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ):
        collection = self.get_or_create_collection(collection_name)

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ):
        collection = self.get_or_create_collection(collection_name)

        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )

    def get_collection_info(self, collection_name: str):
        collection = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata
        }

    def delete_collection(self, collection_name: str):
        self.client.delete_collection(collection_name)

    def list_collections(self):
        return [coll.name for coll in self.client.list_collections()]

    def reset(self):
        self.client.reset()


# Global instance
chroma_client = ChromaClient()