from typing import List, Dict, Any, Optional, Tuple
import json

from app.config import settings, is_groq_model, is_opencode_model
from app.services.chroma_client import chroma_client
from app.services.embed_service import embed_service
from app.services.llm_manager import llm_manager


class RAGService:
    def __init__(self):
        self.collection_map = {
            "test_cases": settings.collection_test_cases,
            "pdf_docs": settings.collection_pdfs,
            "code_base": settings.collection_github
        }

    def search(
        self,
        query: str,
        sources: List[str],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.top_k_chunks
        query_embedding = embed_service.embed_query(query)

        results = []

        for source in sources:
            collection_name = self.collection_map.get(source)
            if not collection_name:
                continue

            try:
                search_results = chroma_client.query(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    n_results=k
                )

                if search_results["documents"]:
                    for i, doc in enumerate(search_results["documents"][0]):
                        results.append({
                            "source": source,
                            "chunk_id": search_results["ids"][0][i],
                            "content": doc,
                            "score": search_results["distances"][0][i] if search_results["distances"] else 0,
                            "metadata": search_results["metadatas"][0][i] if search_results["metadatas"] else {}
                        })
            except Exception as e:
                print(f"Error searching {source}: {e}")
                continue

        results.sort(key=lambda x: x["score"])
        return results[:k * len(sources)]

    def build_context(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int = None
    ) -> str:
        max_t = max_tokens or settings.max_context_tokens
        context = ""

        for chunk in chunks:
            content = chunk["content"]
            if len(context) + len(content) < max_t:
                context += f"\n\n--- From {chunk['source']} ---\n{content}\n"
            else:
                break

        return context.strip()

    def generate_answer(
        self,
        query: str,
        context: str,
        model: str,
        groq_api_key: Optional[str] = None,
        opencode_api_key: Optional[str] = None
    ) -> str:
        system_prompt = f"""You are a QA Copilot assistant for VWO (Visual Website Optimizer) testing.

Your role is to help with:
1. Answering questions about test cases
2. Generating new test cases
3. Debugging test failures
4. Searching documentation

Instructions:
- Use the provided context to answer questions accurately
- Cite sources when possible
- If you cannot find the answer in the context, say so clearly
- Be helpful, concise, and technical when appropriate

Context:
{context}

Answer the user's question based on the context above."""

        try:
            answer = llm_manager.get_response(
                model=model,
                message=query,
                system_prompt=system_prompt,
                groq_api_key=groq_api_key,
                opencode_api_key=opencode_api_key
            )
            return answer
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []

        for chunk in chunks:
            sources.append({
                "source": chunk.get("source", "unknown"),
                "chunk_id": chunk.get("chunk_id", ""),
                "content": chunk.get("content", "")[:500],
                "score": chunk.get("score", 0)
            })

        return sources

    def chat(
        self,
        query: str,
        sources: List[str],
        model: str,
        groq_api_key: Optional[str] = None,
        opencode_api_key: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        chunks = self.search(query, sources)
        context = self.build_context(chunks)

        answer = self.generate_answer(
            query=query,
            context=context,
            model=model,
            groq_api_key=groq_api_key,
            opencode_api_key=opencode_api_key
        )

        formatted_sources = self.format_sources(chunks)

        return answer, formatted_sources


# Global instance
rag_service = RAGService()