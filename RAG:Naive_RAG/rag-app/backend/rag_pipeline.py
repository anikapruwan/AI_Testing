import os
import time
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

class RAGPipeline:
    def __init__(self, vectorstore_dir: str = "../vectorstore"):
        self.vectorstore_dir = vectorstore_dir
        os.makedirs(vectorstore_dir, exist_ok=True)
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        
    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Dict[str, Any]:
        start_time = time.time()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)
        end_time = time.time()
        
        return {
            "chunks": chunks,
            "latency_ms": round((end_time - start_time) * 1000, 2),
            "num_chunks": len(chunks)
        }

    def create_embeddings(self, chunks: List[str]) -> Dict[str, Any]:
        start_time = time.time()
        documents = [Document(page_content=chunk) for chunk in chunks]
        
        # We also get raw embeddings for visualization purposes
        sample_embedding = None
        if chunks:
            sample_embedding = self.embeddings.embed_query(chunks[0])
            
        self.vector_store = QdrantVectorStore.from_documents(
            documents,
            self.embeddings,
            path=self.vectorstore_dir,
            collection_name="rag_collection",
            force_recreate=True
        )
        end_time = time.time()
        
        return {
            "latency_ms": round((end_time - start_time) * 1000, 2),
            "sample_embedding": sample_embedding[:10] if sample_embedding else [],  # first 10 dims
            "vector_dimension": len(sample_embedding) if sample_embedding else 0
        }

    def load_vectorstore(self):
        if os.path.exists(self.vectorstore_dir) and os.listdir(self.vectorstore_dir):
            try:
                self.vector_store = QdrantVectorStore.from_existing_collection(
                    embedding=self.embeddings,
                    collection_name="rag_collection",
                    path=self.vectorstore_dir,
                )
                return True
            except Exception:
                return False
        return False

    def retrieve(self, query: str, k: int = 4) -> Dict[str, Any]:
        start_time = time.time()
        if not self.vector_store:
            loaded = self.load_vectorstore()
            if not loaded:
                raise ValueError("Vector store not initialized or found.")
                
        # Get documents with scores
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)
        
        results = []
        for doc, score in docs_and_scores:
            results.append({
                "content": doc.page_content,
                "score": float(score) # Qdrant uses Cosine Similarity
            })
            
        end_time = time.time()
        
        return {
            "results": results,
            "latency_ms": round((end_time - start_time) * 1000, 2)
        }
