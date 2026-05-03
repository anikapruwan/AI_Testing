"""
Advanced RAG Demo Script

This script demonstrates the core concepts of an advanced RAG system
using open-source components for embeddings, vector storage, and re-ranking.
"""

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class AdvancedRAG:
    def __init__(self, embedding_model_name="BAAI/bge-small-en-v1.5"):
        """
        Initialize the Advanced RAG system with specified components.
        
        Args:
            embedding_model_name (str): Name of the sentence transformer model to use
        """
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize vector database (ChromaDB in this example)
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="advanced_rag_demo",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model_name
            )
        )
        
        # Initialize re-ranker model
        self.reranker_model = SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
    def add_documents(self, documents):
        """
        Add documents to the vector database.
        
        Args:
            documents (list): List of document texts to add
        """
        # Generate IDs for documents
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Add documents to the collection
        self.collection.add(
            documents=documents,
            ids=ids
        )
        print(f"Added {len(documents)} documents to the database.")
        
    def retrieve(self, query, top_k=10):
        """
        Retrieve relevant documents using the vector database.
        
        Args:
            query (str): User query
            top_k (int): Number of documents to retrieve
            
        Returns:
            list: Retrieved documents with similarity scores
        """
        # Query the vector database
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results
        retrieved_docs = []
        for i in range(len(results['ids'][0])):
            retrieved_docs.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'similarity': results['distances'][0][i]
            })
            
        print(f"Retrieved {len(retrieved_docs)} documents from vector database.")
        return retrieved_docs
        
    def rerank(self, query, documents):
        """
        Re-rank documents using a cross-encoder model.
        
        Args:
            query (str): User query
            documents (list): List of documents to re-rank
            
        Returns:
            list: Re-ranked documents with relevance scores
        """
        # Prepare pairs for re-ranking
        pairs = [[query, doc['document']] for doc in documents]
        
        # Compute relevance scores
        scores = self.reranker_model.predict(pairs)
        
        # Add scores to documents and sort
        for i, doc in enumerate(documents):
            doc['relevance_score'] = float(scores[i])
            
        # Sort by relevance score (descending)
        reranked_docs = sorted(documents, key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"Re-ranked {len(reranked_docs)} documents.")
        return reranked_docs
        
    def query(self, query, retrieval_top_k=10, reranking_top_k=5):
        """
        Perform a complete RAG query with retrieval and re-ranking.
        
        Args:
            query (str): User query
            retrieval_top_k (int): Number of documents to initially retrieve
            reranking_top_k (int): Number of documents in final result
            
        Returns:
            dict: Results with retrieved and re-ranked documents
        """
        print(f"Processing query: {query}")
        
        # Step 1: Retrieve documents
        retrieved_docs = self.retrieve(query, retrieval_top_k)
        
        # Step 2: Re-rank documents
        reranked_docs = self.rerank(query, retrieved_docs)
        
        # Step 3: Return top-k re-ranked documents
        final_docs = reranked_docs[:reranking_top_k]
        
        return {
            'query': query,
            'initial_retrieval': retrieved_docs[:retrieval_top_k],
            'reranked_results': final_docs
        }

# Example usage
if __name__ == "__main__":
    # Initialize Advanced RAG system
    rag_system = AdvancedRAG()
    
    # Sample documents (in practice, these would come from PDFs, websites, etc.)
    sample_documents = [
        "Machine learning is a subset of artificial intelligence that focuses on algorithms learning from data.",
        "Deep learning uses neural networks with multiple layers to learn representations of data.",
        "Natural language processing enables computers to understand and interpret human language.",
        "Computer vision allows machines to identify and analyze visual content in images and videos.",
        "Reinforcement learning involves agents learning to make decisions through trial and error interactions.",
        "Data science combines statistics, programming, and domain expertise to extract insights from data.",
        "Neural networks are computing systems inspired by the human brain's interconnected neurons.",
        "Artificial intelligence aims to create systems that can perform tasks requiring human intelligence."
    ]
    
    # Add documents to the system
    rag_system.add_documents(sample_documents)
    
    # Query the system
    query = "How do computers understand human language?"
    results = rag_system.query(query, retrieval_top_k=5, reranking_top_k=3)
    
    # Display results
    print("\n=== QUERY RESULTS ===")
    print(f"Query: {results['query']}")
    print("\nTop re-ranked documents:")
    for i, doc in enumerate(results['reranked_results'], 1):
        print(f"{i}. [Relevance: {doc['relevance_score']:.4f}] {doc['document']}")