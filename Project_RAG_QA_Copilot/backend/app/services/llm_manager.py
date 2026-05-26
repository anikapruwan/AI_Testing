# pyrefly: ignore [missing-import]
from groq import Groq
# pyrefly: ignore [missing-import]
from openai import OpenAI
from typing import Optional, Dict, List
import os

from app.config import settings, is_groq_model, is_opencode_model


class LLMManager:
    def __init__(self):
        self.groq_client = None
        self.opencode_client = None

    def _init_groq(self, api_key: str):
        if not self.groq_client:
            self.groq_client = Groq(api_key=api_key)

    def _init_opencode(self, api_key: str):
        if not self.opencode_client:
            self.opencode_client = OpenAI(api_key=api_key, base_url="https://opencode.ai/zen/go/v1")

    def get_response(
        self,
        model: str,
        message: str,
        system_prompt: str = None,
        groq_api_key: Optional[str] = None,
        opencode_api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        if is_groq_model(model):
            return self._groq_response(
                model=model,
                message=message,
                system_prompt=system_prompt,
                api_key=groq_api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif is_opencode_model(model):
            return self._opencode_response(
                model=model,
                message=message,
                system_prompt=system_prompt,
                api_key=opencode_api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ValueError(f"Unknown model: {model}")

    def _groq_response(
        self,
        model: str,
        message: str,
        system_prompt: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        key = api_key or os.environ.get("GROQ_API_KEY") or settings.groq_api_key
        if not key:
            raise ValueError("Groq API key not provided")

        self._init_groq(key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def _opencode_response(
        self,
        model: str,
        message: str,
        system_prompt: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        key = api_key or os.environ.get("OPENCODE_API_KEY") or settings.opencode_api_key
        if not key:
            raise ValueError("OpenCode API key not provided")

        self._init_opencode(key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = self.opencode_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def validate_api_keys(
        self,
        groq_api_key: Optional[str] = None,
        opencode_api_key: Optional[str] = None
    ) -> Dict[str, bool]:
        results = {
            "groq_valid": False,
            "opencode_valid": False
        }

        if groq_api_key:
            try:
                self._init_groq(groq_api_key)
                self.groq_client.models.list()
                results["groq_valid"] = True
            except Exception as e:
                print(f"Groq validation error: {e}")

        if opencode_api_key:
            try:
                self._init_opencode(opencode_api_key)
                self.opencode_client.models.list()
                results["opencode_valid"] = True
            except Exception as e:
                print(f"OpenCode validation error: {e}")

        return results

    def list_models(self) -> List[Dict]:
        from app.config import ALL_MODELS
        return ALL_MODELS


# Global instance
llm_manager = LLMManager()