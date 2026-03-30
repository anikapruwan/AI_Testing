# Project Constitution (Gemini Schema)

## Architectural Invariants
- 3-Layer Architecture must be followed (Architecture -> Navigation -> Tools).
- All intermediate file operations must use `.tmp/`.
- `tools/` directory is strictly for deterministic scripts.
- Web UI will use vanilla HTML/CSS/JS to communicate with a Python backend (FastAPI/Flask).

## Behavioral Rules
- Provide high-quality, modern glassmorphism UI with dark mode support.
- Ensure all API keys and Jira credentials are treated securely, saved in `.env` or a local secure config file.
- Validate API connections via a dedicated "Test Connection" button before allowing generation.

## Data Schemas

### 1. Settings Schema
```json
{
  "jira_url": "https://your-domain.atlassian.net",
  "jira_email": "user@example.com",
  "jira_api_token": "token",
  "ollama_api_url": "http://localhost:11434",
  "groq_api_key": "gsk_...",
  "claude_api_key": "sk-ant-..."
}
```

### 2. Generate Request Schema
```json
{
  "jira_id": "PROJECT-123",
  "additional_context": "Any extra user instructions...",
  "llm_provider": "groq|ollama|claude"
}
```

### 3. Generate Response Schema
```json
{
  "status": "success",
  "message": "Test plan generated successfully.",
  "download_url": "/api/download/testplan-PROJECT-123.docx",
  "preview_text": "Markdown summary of the generated plan..."
}
```
