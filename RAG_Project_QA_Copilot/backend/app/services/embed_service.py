from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np

from app.config import settings


class EmbedService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None

    def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> List[float]:
        self._load_model()
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        self._load_model()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_text(query)

    @property
    def embedding_dimension(self) -> int:
        self._load_model()
        return self.model.get_sentence_embedding_dimension()


# Global instance
embed_service = EmbedService()