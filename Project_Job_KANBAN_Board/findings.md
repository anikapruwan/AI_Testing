# Findings — Job Application Kanban Board

## Research
- Local-only architecture chosen — no external APIs required
- Flask selected over FastAPI due to Python 3.14 compatibility (no pydantic-core wheels yet)
- JSON file store in .tmp/ serves as IndexedDB analog for server-side persistence

## Decisions
- 7 states with strict transition rules, plus universal override to done_archived
- offer_received and offer_not_received added per user request
- HR contacts stored as array of {name, email, phone} per job card
- All mutations auto-saved — no save button needed
