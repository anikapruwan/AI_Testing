import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
from tools.jira_fetcher import fetch_jira_ticket, test_jira_connection
from tools.llm_router import route_to_llm, test_llm_connection, build_prompt
from tools.docx_generator import generate_docx
from tools.pdf_generator import generate_pdf

app = FastAPI(title="AI Test Planner Agent")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class Settings(BaseModel):
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    ollama_api_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    claude_api_key: str = ""

class GenerateRequest(BaseModel):
    jira_id: str
    additional_context: str = ""
    llm_provider: str

class TestConnectionRequest(BaseModel):
    provider: str

# Configs
SETTINGS_FILE = ".env_settings.json"
TEMPLATE_FILE = "Testplan_Template/Test Plan - Template.docx"

def load_settings() -> Settings:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return Settings(**json.load(f))
    return Settings()

@app.get("/api/settings")
def get_settings():
    return load_settings().model_dump()

@app.post("/api/settings")
def save_settings(settings: Settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings.model_dump(), f)
    return {"status": "success"}

@app.post("/api/test-connection")
def test_connection(req: TestConnectionRequest):
    settings = load_settings()
    if req.provider == "jira":
        success, msg = test_jira_connection(settings.jira_url, settings.jira_email, settings.jira_api_token)
    else:
        success, msg = test_llm_connection(req.provider, settings.ollama_api_url, settings.ollama_model, settings.groq_api_key, settings.groq_model, settings.claude_api_key)
        
    return {"status": "success" if success else "error", "message": msg}

@app.post("/api/generate")
def generate_test_plan(req: GenerateRequest):
    try:
        settings = load_settings()
        
        # 1. Fetch Jira Context
        logger.info(f"Fetching Jira ticket: {req.jira_id}")
        jira_context = fetch_jira_ticket(req.jira_id, settings.jira_url, settings.jira_email, settings.jira_api_token)
        
        # 2. Build Prompt
        prompt = build_prompt(jira_context, req.additional_context)
        
        # 3. Route to LLM
        logger.info(f"Routing prompt to {req.llm_provider}")
        llm_response = route_to_llm(prompt, req.llm_provider, settings.ollama_api_url, settings.ollama_model, settings.groq_api_key, settings.groq_model, settings.claude_api_key)
        
        # 4. Generate DOCX and PDF
        output_filename = f"testplan-{req.jira_id}.docx"
        output_path = f".tmp/{output_filename}"
        generate_docx(llm_response, output_path, TEMPLATE_FILE)
        
        pdf_filename = f"testplan-{req.jira_id}.pdf"
        pdf_path = f".tmp/{pdf_filename}"
        generate_pdf(llm_response, pdf_path)
        
        return {
            "status": "success", 
            "message": "Generation completed successfully.",
            "download_url": f"/api/download/{output_filename}",
            "download_url_pdf": f"/api/download/{pdf_filename}",
            "preview_text": llm_response
        }
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
def download_file(filename: str):
    path = f".tmp/{filename}"
    if os.path.exists(path):
        return FileResponse(path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

# Serve frontend
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
