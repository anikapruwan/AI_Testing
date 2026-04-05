# 🔍 Findings & Discoveries

## Initial Context
- Framework: B.L.A.S.T
- App is a UI-driven Test Planner Agent.
- User will supply inputs on-the-fly (Jira settings, LLM settings, ticket ID).
- Output must be based on `Test Plan - Template.docx`.

## Constraints & Rules
- Must test connections before heavy logic runs.
- JSON structure is strictly defined in `gemini.md`.
