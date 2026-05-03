from typing import Optional, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
import time

class LLMProvider:
    def __init__(self, provider: str = "groq", api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = self._initialize_client()

    def _initialize_client(self):
        if self.provider.lower() == "groq":
            if not self.api_key:
                raise ValueError("Groq API key is required for Groq provider.")
            return ChatGroq(temperature=0.7, groq_api_key=self.api_key, model_name=self.model)
        elif self.provider.lower() == "ollama":
            # Using locally running Ollama
            return ChatOllama(model=self.model, temperature=0.7)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate(self, prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            response = self.client.invoke([HumanMessage(content=prompt)])
            end_time = time.time()
            return {
                "success": True,
                "content": response.content,
                "latency_ms": round((end_time - start_time) * 1000, 2),
                "provider": self.provider,
                "model": self.model
            }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "latency_ms": round((end_time - start_time) * 1000, 2),
                "provider": self.provider,
                "model": self.model
            }
