# Advanced RAG Implementation

This folder contains the implementation of an advanced Retrieval-Augmented Generation (RAG) system using open-source components.

## Key Components

### 1. Open Source Embeddings

#### a) Sentence Transformers
- **Model**: `all-MiniLM-L6-v2`, `all-mpnet-base-v2`
- **Description**: Fast and efficient sentence embeddings
- **Pros**: Good performance, fast encoding
- **Cons**: Requires computational resources for large datasets

#### b) Instructor Models
- **Model**: `hkunlp/instructor-large`, `hkunlp/instructor-xl`
- **Description**: Instruction-tuned embeddings for specific tasks
- **Pros**: Better performance for specific domains with proper instructions
- **Cons**: Slower than sentence transformers

#### c) E5 Models
- **Model**: `intfloat/e5-small-v2`, `intfloat/e5-base-v2`, `intfloat/e5-large-v2`
- **Description**: State-of-the-art embeddings with query-document distinction
- **Pros**: Excellent performance, different encoders for queries vs documents
- **Cons**: Larger models require more resources

#### d) BGEM models
- **Model**: `BAAI/bge-small-en-v1.5`, `BAAI/bge-base-en-v1.5`
- **Description**: Efficient and effective embeddings from BAAI
- **Pros**: Good balance between performance and efficiency
- **Cons**: May require fine-tuning for domain-specific applications

### 2. Open Source Vector Databases

#### a) ChromaDB
- **Description**: Easy-to-use vector database with persistent storage
- **Pros**: Simple setup, Python-native, good for small to medium datasets
- **Cons**: Not optimized for large-scale production environments

#### b) FAISS (Facebook AI Similarity Search)
- **Description**: Efficient similarity search and clustering of dense vectors
- **Pros**: Very fast, optimized for large-scale similarity search
- **Cons**: In-memory by default, requires extra work for persistence

#### c) Weaviate
- **Description**: Vector search engine with built-in ML model hosting
- **Pros**: Hybrid search (vector + keyword), GraphQL API, cloud-native
- **Cons**: More complex setup, higher resource usage

#### d) Qdrant
- **Description**: Vector similarity search engine with extended filtering
- **Pros**: Rich filtering options, REST/gRPC APIs, scalable
- **Cons**: Requires more configuration than Chroma

#### e) Pinecone (Open Source Tier)
- **Description**: Managed vector database with generous free tier
- **Pros**: Fully managed, scalable, good performance
- **Cons**: Limited free tier, partially managed service

### 3. Open Source Re-rankers

#### a) Cross-Encoder Models
- **Models**: `cross-encoder/ms-marco-MiniLM-L-6-v2`, `cross-encoder/ms-marco-MiniLM-L-12-v2`
- **Description**: Fine-tuned models for passage ranking
- **Pros**: Excellent accuracy for relevance scoring
- **Cons**: Slower than bi-encoder models, computationally intensive

#### b) ColBERT
- **Description**: Contextual Late Interaction over BERT for ranking
- **Pros**: Highly accurate, efficient interaction mechanism
- **Cons**: Complex implementation, requires training data

#### c) Sentence Transformers with Re-ranking
- **Models**: `sentence-transformers/ms-marco-MiniLM-L-12-v2`, `sentence-transformers/ms-marco-MiniLM-L-6-v2`
- **Description**: Pre-trained models specifically designed for re-ranking
- **Pros**: Good balance between performance and speed
- **Cons**: Still slower than initial retrieval methods

#### d) TART (Token-Aware Relevance Transformer)
- **Description**: Context-aware document ranking
- **Pros**: State-of-the-art performance on several benchmarks
- **Cons**: Newer technology, less community support

## Recommended Architecture

```
PDF/Documents → Text Processing → Embedding Model → Vector Database
                                                    ↓
Query → Initial Retrieval → Re-ranker → Final Results → LLM
```

### Implementation Plan:

1. **Text Processing**:
   - Chunking with overlapping windows
   - Content extraction from PDFs/HTML/documents
   - Metadata extraction

2. **Embedding Layer**:
   - Use `BAAI/bge-small-en-v1.5` for initial implementation
   - Can switch to `intfloat/e5-small-v2` for better performance

3. **Vector Database**:
   - Start with ChromaDB for simplicity
   - Migrate to Qdrant or Weaviate for production needs

4. **Re-ranking Component**:
   - Implement `cross-encoder/ms-marco-MiniLM-L-6-v2` for re-ranking
   - This model provides excellent performance with reasonable speed

5. **LLM Integration**:
   - Use local models like LLaMA variants through HuggingFace
   - Or cloud services like Groq/Ollama for better performance

## Getting Started

1. Install dependencies:
```bash
pip install sentence-transformers chromadb qdrant-client faiss-cpu transformers torch
```

2. Choose your components based on your specific use case and performance requirements.