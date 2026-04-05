# LLM Generation SOP

## Goal
To generate a comprehensive Test Plan matching the structure of `Test Plan - Template.docx` by providing the LLM with the Jira intermediate payload and additional context.

## Inputs
- `provider`: Ollama / Groq / Grok
- `base_url`: URL for local LLM (Ollama)
- `api_key`: API Key for cloud API
- `model`: Target model string
- `ticket_payload`: Intermediate Jira JSON payload
- `additional_context`: Additional testing requirements

## Process
1. Construct the System Prompt instructing the LLM to act as a Senior QA Architect.
2. Provide the template constraints: Explain the sections required by `Test Plan - Template.docx` (e.g., Objectives, Scope, Test Strategy, Entry/Exit criteria).
3. Insert `ticket_payload` and `additional_context` into the user prompt.
4. Send completion request using standard `messages` array syntax (compatible with OpenAI format or standard Ollama generate format).
5. Ensure response is cleanly formatted Markdown without unnecessary conversational text.

## Outputs
Extract and return the Markdown payload representing the Test Plan.

## Edge Cases
- Timeout: Ensure 60+ seconds is allowed for the LLM to generate long Markdown.
- Rate Limits: Handle 429 errors gracefully if using Groq API.
