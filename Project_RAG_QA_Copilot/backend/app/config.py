import os
from pathlib import Path
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
# pyrefly: ignore [missing-import]
from pydantic import Field


class Settings(BaseSettings):
    # API Keys
    groq_api_key: Optional[str] = Field(None, alias="GROQ_API_KEY")
    opencode_api_key: Optional[str] = Field(None, alias="OPENCODE_API_KEY")

    # ChromaDB
    chroma_persist_dir: str = Field("./data/chroma", alias="CHROMA_PERSIST_DIR")

    # Embeddings
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(384)

    # RAG Settings
    default_model: str = Field("llama-3.3-70b-versatile", alias="DEFAULT_MODEL")
    max_context_tokens: int = Field(8000)
    top_k_chunks: int = Field(10)

    # Server
    backend_host: str = Field("0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(8000, alias="BACKEND_PORT")
    frontend_port: int = Field(5173, alias="FRONTEND_PORT")

    # Data Paths
    csv_data_path: str = Field("/Users/anirudhkapruwan/AI_Training/Antigravity/RAG:Advance_RAG/data/uploads/testcases_vwo.csv")
    pdf_data_path: str = Field("/Users/anirudhkapruwan/AI_Training/Antigravity/Live_Class/Chapter_08_RAG/Basic_RAG_EXPLAIN/data/Product Requirements Document_VWO.pdf")
    github_repo_url: str = Field("https://github.com/PramodDutta/AdvanceSeleniumFrameworkTTA")

    # Collections
    collection_test_cases: str = "test_cases"
    collection_pdfs: str = "pdf_docs"
    collection_github: str = "code_base"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# Ensure chroma directory exists
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


# Available Models
GROQ_MODELS = [
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Recommended)", "provider": "Groq"},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Fast)", "provider": "Groq"},
    {"id": "llama-3.2-90b-vision-preview", "name": "Llama 3.2 90B Vision", "provider": "Groq"},
    {"id": "llama-3.2-11b-vision-preview", "name": "Llama 3.2 11B Vision", "provider": "Groq"},
    {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "provider": "Groq"},
    {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "provider": "Groq"},
]

OPENCODE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o (Best Quality)", "provider": "OpenCode"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Cheap)", "provider": "OpenCode"},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenCode"},
    {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet", "provider": "OpenCode"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "OpenCode"},
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "OpenCode"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "OpenCode"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "OpenCode"},
    {"id": "deepseek-chat", "name": "DeepSeek V3", "provider": "OpenCode"},
    {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "OpenCode"},
    {"id": "big-pickle", "name": "Big Pickle", "provider": "OpenCode"},
    {"id": "deepseek-v4-flash-free", "name": "DeepSeek V4 Flash Free", "provider": "OpenCode"},
    {"id": "minimax-m2.5-free", "name": "MiniMax M2.5 Free", "provider": "OpenCode"},
    {"id": "ring-2.6-1t-free", "name": "Ring 2.6 1T Free", "provider": "OpenCode"},
    {"id": "nemotron-3-super-free", "name": "Nemotron 3 Super Free", "provider": "OpenCode"},
]

ALL_MODELS = GROQ_MODELS + OPENCODE_MODELS


def get_model_by_id(model_id: str):
    for model in ALL_MODELS:
        if model["id"] == model_id:
            return model
    return None


def is_groq_model(model_id: str) -> bool:
    model = get_model_by_id(model_id)
    return model and model["provider"] == "Groq"


def is_opencode_model(model_id: str) -> bool:
    model = get_model_by_id(model_id)
    return model and model["provider"] == "OpenCode"