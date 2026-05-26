# Task Plan — Job Application Kanban Board

## Phases

### Phase 1: Blueprint
- [x] Answer 5 discovery questions
- [x] Define JSON data schema in gemini.md
- [x] Research relevant GitHub repos / resources

### Phase 2: Link
- [x] Set up .env (no external APIs needed)
- [x] Connection verification (local-only, no handshake needed)

### Phase 3: Architect
- [x] Write architecture SOPs in architecture/
- [x] Build deterministic Python backend (Flask + JSON store)
- [x] Implement state management engine with strict transitions

### Phase 4: Stylize
- [x] Build vibe-coded Kanban UI (HTML/CSS/JS)
- [x] Implement drag-and-drop state transitions
- [x] Seed demo data

### Phase 5: Trigger
- [x] Run server on port 8000
- [x] Verify all CRUD + transition endpoints
- [x] Finalize documentation

## Goals
- Parse job descriptions and auto-extract metadata
- Track resume versions per application
- Maintain 5-state Kanban pipeline: Wishlist → Applied → Interviewing → Negotiating → Done/Archived
- Natural language state updates
- Sleek, minimalist interactive UI
