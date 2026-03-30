import requests
import json

def route_to_llm(prompt: str, provider: str, ollama_url: str, ollama_model: str, groq_key: str, groq_model: str, claude_key: str):
    """
    Routes the prompt to the selected LLM provider and returns the string response.
    """
    if provider == "ollama":
        if not ollama_url:
            raise ValueError("Ollama URL is missing.")
        # Using a default common model for Ollama
        url = f"{ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": ollama_model or "llama3",
            "prompt": prompt,
            "stream": False
        }
        res = requests.post(url, json=payload, timeout=600)
        if res.status_code == 200:
            return res.json().get("response", "")
        raise Exception(f"Ollama error: {res.text}")
        
    elif provider == "groq":
        if not groq_key:
            raise ValueError("Groq API Key is missing.")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": groq_model or "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=600)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        raise Exception(f"Groq error: {res.text}")
        
    elif provider == "claude":
        if not claude_key:
            raise ValueError("Claude API Key is missing.")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": claude_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=600)
        if res.status_code == 200:
            return res.json()["content"][0]["text"]
        raise Exception(f"Claude error: {res.text}")
        
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

def test_llm_connection(provider: str, ollama_url: str, ollama_model: str, groq_key: str, groq_model: str, claude_key: str):
    """
    Test connection to the selected provider.
    """
    try:
        route_to_llm("Respond with 'OK'", provider, ollama_url, ollama_model, groq_key, groq_model, claude_key)
        return True, f"{provider.capitalize()} connected successfully."
    except Exception as e:
        return False, f"{provider.capitalize()} error: {str(e)}"

def build_prompt(jira_context: dict, additional_context: str) -> str:
    """
    Constructs the master prompt using the parsed Jira ticket and any user inputs.
    """
    import os
    summary = jira_context.get("summary", "N/A")
    description = jira_context.get("description", "N/A")
    
    prompt_path = "Testplan_Template/prompt.md"
    base_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    else:
        base_prompt = "You are an expert QA Engineer. Generate a Test Plan based on the Jira ticket."
    
    prompt = f"""{base_prompt}
    
---
CURRENT JIRA TICKET INFORMATION:
Summary: {summary}
Description: {description}

ADDITIONAL USER CONTEXT:
{additional_context}

IMPORTANT: Please base your output specifically on the above Current Jira Ticket Information, supplementing the instructions and expectations mentioned earlier. Ensure the output is clean Markdown format. Do NOT output any conversational text.
"""
    return prompt.strip()
