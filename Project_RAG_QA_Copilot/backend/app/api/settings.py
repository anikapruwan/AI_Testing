from fastapi import APIRouter, HTTPException
from typing import Optional, Dict
import os

from app.models.settings import (
    SettingsRequest,
    SettingsResponse,
    ValidateKeysRequest,
    ValidateKeysResponse,
    APIKeys
)
from app.config import settings, ALL_MODELS
from app.services.llm_manager import llm_manager

router = APIRouter()

_api_keys_store = {
    "groq_api_key": None,
    "opencode_api_key": None,
    "default_model": settings.default_model
}


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    return SettingsResponse(
        default_model=_api_keys_store["default_model"],
        groq_api_key_set=bool(_api_keys_store["groq_api_key"]),
        opencode_api_key_set=bool(_api_keys_store["opencode_api_key"]),
        available_models=ALL_MODELS
    )


@router.post("/settings")
async def update_settings(request: SettingsRequest):
    if request.api_keys:
        if request.api_keys.groq_api_key:
            _api_keys_store["groq_api_key"] = request.api_keys.groq_api_key
            os.environ["GROQ_API_KEY"] = request.api_keys.groq_api_key

        if request.api_keys.opencode_api_key:
            _api_keys_store["opencode_api_key"] = request.api_keys.opencode_api_key
            os.environ["OPENCODE_API_KEY"] = request.api_keys.opencode_api_key

    if request.default_model:
        _api_keys_store["default_model"] = request.default_model

    return {
        "status": "success",
        "message": "Settings updated",
        "default_model": _api_keys_store["default_model"]
    }


@router.post("/validate-keys", response_model=ValidateKeysResponse)
async def validate_keys(request: ValidateKeysRequest):
    result = llm_manager.validate_api_keys(
        groq_api_key=request.groq_api_key,
        opencode_api_key=request.opencode_api_key
    )

    return ValidateKeysResponse(
        groq_valid=result.get("groq_valid", False),
        opencode_valid=result.get("opencode_valid", False),
        groq_model_name="llama-3.3-70b-versatile" if result.get("groq_valid") else None,
        opencode_model_name="gpt-4o" if result.get("opencode_valid") else None
    )


@router.get("/keys-status")
async def keys_status():
    return {
        "groq_api_key_set": bool(_api_keys_store.get("groq_api_key")),
        "opencode_api_key_set": bool(_api_keys_store.get("opencode_api_key")),
        "default_model": _api_keys_store.get("default_model")
    }