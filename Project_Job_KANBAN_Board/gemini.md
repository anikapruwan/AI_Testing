# Project Constitution — Job Application Kanban Board

## North Star
End-to-end job tracking Kanban board — a local web app with a Python server backend.

## Data Schema

### Job Application (Input/Output)
```json
{
  "id": "uuid-string",
  "company": "string (required)",
  "role": "string (required)",
  "date_applied": "ISO-8601 date (required)",
  "key_requirements": ["string"],
  "resume_version": "string | null",
  "state": "wishlist | applied | interviewing | negotiating | offer_received | offer_not_received | done_archived",
  "hr_contacts": [
    {
      "name": "string",
      "email": "string",
      "phone": "string"
    }
  ],
  "notes": "string",
  "created_at": "ISO-8601 datetime",
  "updated_at": "ISO-8601 datetime"
}
```

### Valid State Transitions
```
wishlist       → applied
applied        → interviewing
interviewing   → negotiating
negotiating    → offer_received | offer_not_received
offer_received → done_archived
offer_not_received → done_archived
```
Any state can transition to `done_archived` as a manual override.

## Behavioral Rules
- **Auto-save**: Every mutation persists instantly to IndexedDB. No manual save button.
- **Strict state transitions**: Jobs can only move via defined transitions above. Invalid moves are rejected.
- **Mandatory fields**: Company name, role, and date_applied are required for creation.
- **Local-only**: No data leaves the browser. No external API calls.
- **HR contacts**: Each job card stores recruiter/HR name, email, and phone for future reference.

## Architectural Invariants
- Backend: TypeScript + Express (server/)
- Frontend: React + Vite + TypeScript (client/)
- Storage: JSON file in .tmp/jobs.json
- No external dependencies beyond npm packages
- All state logic must be deterministic — no LLM guessing at runtime
