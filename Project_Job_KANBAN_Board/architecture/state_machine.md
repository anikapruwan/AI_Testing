# State Machine SOP — Job Application Kanban

## Valid States
1. `wishlist` — Jobs you're interested in but haven't applied to
2. `applied` — Application submitted
3. `interviewing` — In the interview process
4. `negotiating` — Offer stage / salary discussion
5. `offer_received` — Got the offer
6. `offer_not_received` — Rejected or ghosted
7. `done_archived` — Closed (archived from any state)

## State Transitions (Strict)
```
wishlist       → applied
applied        → interviewing
interviewing   → negotiating
negotiating    → offer_received
negotiating    → offer_not_received
offer_received → done_archived
offer_not_received → done_archived
```

## Override Rule
Any state can be manually moved to `done_archived` as a bypass (e.g., job posting closed, company folded).

## Field Requirements
- `company` — required, non-empty string
- `role` — required, non-empty string
- `date_applied` — required, ISO-8601 date
- `hr_contacts` — optional array of {name, email, phone}
- `notes` — optional string
- `resume_version` — optional string
- `key_requirements` — optional array of strings

## Edge Cases
- Moving to same state: no-op, returns success
- Invalid transition: returns 400 with allowed next states
- Missing required fields on create: returns 422
