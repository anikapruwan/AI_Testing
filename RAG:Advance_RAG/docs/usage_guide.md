# Advanced RAG Usage Guide

This guide explains how to implement and use the advanced RAG components in your projects.

## Installation

To get started with the advanced RAG implementation, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Components Overview

### 1. Embedding Models

We recommend starting with BGE (Bidirectional Guided Encoder) models for a good balance of performance and efficiency:

```python
from sentence_transformers import SentenceTransformer

# Initialize the embedding model
embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# Generate embeddings
documents = ["Document 1 text...", "Document 2 text..."]
embeddings = embedding_model.encode(documents)
```

### 2. Vector Databases

Choose a vector database based on your scalability needs:

#### ChromaDB (Development/Small Scale)
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_collection")

# Add documents
collection.add(
    documents=["Document text..."],
    ids=["doc1"]
)

# Query documents
results = collection.query(
    query_texts=["Search query..."],
    n_results=5
)
```

#### Qdrant (Production Scale)
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(":memory:")  # or provide host
client.recreate_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Add documents
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(id=1, vector=embedding, payload={"text": "Document text..."})
    ]
)
```

### 3. Re-rankers

Implement re-ranking with cross-encoder models for improved result relevance:

```python
from sentence_transformers import CrossEncoder

# Initialize re-ranker
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Re-rank documents
query = "Search query..."
documents = ["Doc 1...", "Doc 2...", "Doc 3..."]
pairs = [[query, doc] for doc in documents]
scores = reranker.predict(pairs)

# Sort documents by relevance
ranked_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

## Complete Workflow

1. **Document Processing**:
   - Extract text from sources (PDFs, web pages, etc.)
   - Split into chunks with appropriate overlap
   - Generate embeddings using your chosen model

2. **Indexing**:
   - Store embeddings and document metadata in your vector database
   - Ensure proper indexing for fast retrieval

3. **Query Processing**:
   - Encode the user query using the same embedding model
   - Retrieve top-K documents from the vector database
   - Apply re-ranking to improve result relevance

4. **Result Presentation**:
   - Present final ranked results to the user
   - Optionally, use an LLM to generate a synthesized answer

## Performance Considerations

1. **Embedding Model Selection**:
   - For real-time applications: Use smaller, faster models
   - For accuracy-critical applications: Use larger, more accurate models
   - Consider domain-specific fine-tuned models

2. **Vector Database Optimization**:
   - Use approximate nearest neighbor search for large datasets
   - Implement proper indexing strategies
   - Monitor memory usage and disk I/O

3. **Re-ranking Efficiency**:
   - Only re-rank top-K retrieved results (typically 10-20)
   - Cache re-ranker results for frequently asked questions
   - Consider using GPU acceleration for re-ranker models

## Next Steps

1. Start with the demo script in `src/advanced_rag_demo.py`
2. Experiment with different combinations of models from `config/models_config.yaml`
3. Test performance with your specific dataset and use case
4. Monitor latency and accuracy to optimize your implementation