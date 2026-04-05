# 🚀 B.L.A.S.T. Project Constitution

## 1. Project Goal (North Star)
Intelligent Test Plan Creator: An agent that dynamically connects to a ticket management system (like Jira or ADO), fetches a user story based on an ID, and generates a Test Plan using a requested `.docx` template.

## 2. Integrations
- **Jira/ADO** (On-the-fly connection settings)
- **LLM Providers** (Ollama, GROQ, Grok - On-the-fly connection settings)

## 3. Data Schemas

### Input Payload (App / User interface -> Agent)
```json
{
  "ticket_system": {
    "provider": "Jira",
    "url": "https://company.atlassian.net",
    "email": "user@example.com",
    "api_token": "secret_token",
    "ticket_id": "TEST-123"
  },
  "llm_settings": {
    "provider": "Ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3",
    "api_key": ""
  },
  "additional_context": "Focus on security testing for this feature."
}
```

### Intermediate Payload (Ticket System -> Agent)
```json
{
  "ticket_id": "TEST-123",
  "title": "Implement User Login",
  "description": "As a user, I want to log in using email and password so I can access my dashboard.",
  "acceptance_criteria": "1. Valid credentials grant access. 2. Invalid credentials show error."
}
```

### Output Payload (Agent -> Delivery)
```json
{
  "status": "success",
  "message": "Test plan generated successfully.",
  "test_plan_content_markdown": "# Test Plan...\n...",
  "file_path": "/outputs/TEST-123_Test_Plan.docx"
}
```

## 4. Behavioral Rules
- Verify "Test Connection" buttons for Jira and LLM.
- Use the overarching `Test Plan - Template.docx` for structuring the output.
- Never guess the Jira ID or the LLM settings; they must be provided.
