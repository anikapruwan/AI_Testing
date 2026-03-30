# Findings

## Research
- **App Type**: Test Case Generator (API and Web App, Functional and Non-functional).
- **Input Mechanism**: User provides Jira requirements via copy-paste or chat input.
- **Output Format**: Jira format test cases (functional and non-functional).

## Discoveries
- **Tech Stack**:
    - Backend: Node.js with TypeScript
    - Frontend: React (TypeScript)
- **Local LLM Infrastructure Supported**:
    - Ollama API
    - LM Studio API
    - Groq API (Note: Image says Groq, user previously mentioned Grok)
    - OpenAI API
    - Claude API
    - Gemini API
- **UI Design (from wireframe)**:
    - **Main Interface**: A left sidebar for "History", a main central area to display generated Test Cases, and an input box at the bottom for Jira requirements ("Ask here...").
    - **Settings Interface**: A section or modal for configuring API keys/settings (specifically mentioning Ollama, Groq, and OpenAI), along with a "Test Connection" button and a "Save Button".

## Constraints
- **Execution**: Forbidden from writing scripts or code until Discovery Questions are answered and Blueprint in `task_plan.md` is approved.
