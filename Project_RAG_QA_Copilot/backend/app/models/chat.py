from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    model: Optional[str] = Field(None, description="Model to use")
    sources: Optional[List[str]] = Field(
        default=["test_cases", "pdf_docs", "code_base"],
        description="Which sources to search"
    )
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")


class SourceCitation(BaseModel):
    source: str = Field(..., description="Source name (e.g., test_cases, pdf_docs)")
    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Relevant content chunk")
    score: Optional[float] = Field(None, description="Relevance score")


class ChatResponse(BaseModel):
    message: str = Field(..., description="AI response")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    model_used: str = Field(..., description="Model that generated the response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    sources: Optional[List[str]] = Field(
        default=["test_cases", "pdf_docs", "code_base"],
        description="Which sources to search"
    )
    top_k: Optional[int] = Field(5, description="Number of results to return")


class SearchResult(BaseModel):
    source: str
    chunk_id: str
    content: str
    score: float