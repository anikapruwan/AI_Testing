# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict


class APIKeys(BaseModel):
    groq_api_key: Optional[str] = Field(None, description="Groq API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")

    @model_validator(mode='after')
    def check_at_least_one_key(self):
        if not self.groq_api_key and not self.openai_api_key:
            raise ValueError('At least one API key (Groq or OpenAI) must be provided.')
        return self


class SettingsRequest(BaseModel):
    api_keys: Optional[APIKeys] = Field(None, description="API keys to update")
    default_model: Optional[str] = Field(None, description="Default model to use")


class SettingsResponse(BaseModel):
    default_model: str
    groq_api_key_set: bool
    openai_api_key_set: bool
    available_models: list


class ValidateKeysRequest(BaseModel):
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    @model_validator(mode='after')
    def check_at_least_one_key(self):
        if not self.groq_api_key and not self.openai_api_key:
            raise ValueError('At least one API key (Groq or OpenAI) must be provided.')
        return self


class ValidateKeysResponse(BaseModel):
    groq_valid: bool
    groq_model_name: Optional[str] = None
    openai_valid: bool
    openai_model_name: Optional[str] = None


class IngestRequest(BaseModel):
    source_type: str = Field(..., description="csv, pdf, or github")
    source_path: Optional[str] = Field(None, description="Path to source (for local files)")
    repo_url: Optional[str] = Field(None, description="GitHub repository URL")
    github_token: Optional[str] = Field(None, description="GitHub personal access token")


class IngestResponse(BaseModel):
    status: str
    message: str
    documents_ingested: int = 0
    chunks_created: int = 0