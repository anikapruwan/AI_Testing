# Jira Fetch SOP

## Goal
Fetch a Jira ticket's title, description, and acceptance criteria based on its Jira ID.

## Inputs
- `url`: Base URL of the Jira instance
- `email`: Authenticated user email
- `api_token`: Jira API Token
- `ticket_id`: Target Jira Issue Key (e.g., TEST-123)

## Process
1. Validate inputs (ensure URL has http/https).
2. Construct endpoint: `GET {url}/rest/api/3/issue/{ticket_id}`
3. Send authenticated request with `Content-Type: application/json`.
4. Parse response:
   - Extract `.fields.summary` as Title.
   - Extract `.fields.description` (Jira ADF format). Needs to be converted to plain text for LLM consumption.
   - Extract acceptance criteria (usually a custom field or embedded in description).

## Outputs
Returns a minimal JSON object matching `Intermediate Payload` in `gemini.md`.

## Edge Cases
- Invalid credentials: Return HTTP 401. Provide clear error.
- Ticket not found: Return HTTP 404.
- Jira format parsing: Description might be rich text (ADF). If ADF, convert to string safely.
