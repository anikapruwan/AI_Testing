# Task Plan: AI Test Planner Agent

## Phase 1: B - Blueprint
- [ ] Answer Discovery Questions.
- [ ] Define the JSON Data Schema in `gemini.md`.
- [ ] Get the Blueprint approved.

## Phase 2: L - Link
- [ ] Verify API credentials (Jira API, etc.).
- [ ] Build minimal scripts to verify Jira extraction.

## Phase 3: A - Architect
- [ ] Document Architecture in `architecture/` SOPs.
- [ ] Ensure deterministic business logic separate from LLM layer.
- [ ] Set up Tools in `tools/` for parsing Docx, Vision on UI screenshot, Jira fetching, and Docx creation.

## Phase 4: S - Stylize
- [ ] Format the final output into the desired Testplan format (e.g., DOCX).

## Phase 5: T - Trigger
- [ ] Finalize deployment logic.

**Notes:** Do not build scripts until the Blueprint and Data Schema are defined.
