from fastapi import APIRouter, HTTPException
from typing import List

from app.models.chat import SearchRequest, SearchResult
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    sources = request.sources or ["test_cases", "pdf_docs", "code_base"]

    try:
        results = rag_service.search(
            query=request.query,
            sources=sources,
            top_k=request.top_k
        )

        formatted_results = [
            SearchResult(
                source=r["source"],
                chunk_id=r["chunk_id"],
                content=r["content"],
                score=r["score"]
            )
            for r in results
        ]

        return formatted_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def list_sources():
    return {
        "sources": [
            {
                "id": "test_cases",
                "name": "Test Cases (CSV)",
                "description": "5000 test cases for VWO"
            },
            {
                "id": "pdf_docs",
                "name": "PDF Documentation",
                "description": "Product Requirements Document"
            },
            {
                "id": "code_base",
                "name": "Selenium Code",
                "description": "GitHub repository source code"
            }
        ]
    }