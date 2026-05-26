from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List

from app.models.chat import ChatRequest, ChatResponse, SourceCitation
from app.services.rag_service import rag_service
from app.config import settings

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    model = request.model or settings.default_model
    sources = request.sources or ["test_cases", "pdf_docs", "code_base"]

    groq_key = request.extra.get("groq_api_key") if hasattr(request, "extra") else None
    openai_key = request.extra.get("opencode_api_key") if hasattr(request, "extra") else None

    try:
        answer, sources_list = rag_service.chat(
            query=request.message,
            sources=sources,
            model=model,
            groq_api_key=groq_key,
            opencode_api_key=openai_key
        )

        formatted_sources = [
            SourceCitation(
                source=s["source"],
                chunk_id=s["chunk_id"],
                content=s["content"],
                score=s["score"]
            )
            for s in sources_list
        ]

        return ChatResponse(
            message=answer,
            sources=formatted_sources,
            model_used=model,
            conversation_id=request.conversation_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/with-keys")
async def chat_with_keys(
    message: str = Body(...),
    model: str = Body(...),
    sources: List[str] = Body(...),
    groq_api_key: Optional[str] = Body(None),
    opencode_api_key: Optional[str] = Body(None)
):
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not groq_api_key and not opencode_api_key:
        raise HTTPException(status_code=400, detail="At least one API key required")

    try:
        answer, sources_list = rag_service.chat(
            query=message,
            sources=sources,
            model=model,
            groq_api_key=groq_api_key,
            opencode_api_key=opencode_api_key
        )

        return {
            "message": answer,
            "sources": sources_list,
            "model_used": model
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))