# Block C — AI Analysis (initial implementation)

## Trust boundary
- `config/freelancer-profile.json` must contain **verified** claims only. Copy from
  `config/freelancer-profile.example.json`, edit proofs, and keep the real profile local.
- The profile is not committed: `.gitignore` excludes it. Container mounts the
  `config/` directory read-only. Do not store credentials in the profile.
- Opportunity text is untrusted. The OpenAI system prompt instructs the model to
  ignore instructions inside it; this is a mitigation, **not a guarantee**.
- Responses are validated; matched skill names must be present in the verified profile.
- Drafts are never sent automatically. All results require human review.

## Modes
- `offline`: deterministic exact-skill keyword matching, **not** semantic AI.
  No external calls, no API costs.
- `openai`: opt-in, requires `OPENAI_API_KEY` in local `.env`, and a supported
  `AI_MODEL` (`gpt-4o-mini` default or `gpt-4.1-mini`). The request uses a
  bounded input (300 title + 8000 description chars), 750 output tokens,
  30-second timeout, no automatic retries. **A hard daily budget and persistent
  usage accounting are not yet implemented.** Do not expose this endpoint to
  untrusted users or run automated batches.

## API
`POST /api/v1/analysis` with header `X-Admin-Token` and JSON
`{"opportunity_id": 1, "mode": "offline"}`. Returns a score, rationale,
verified matched skills, warnings and draft. Results are stored in the
`opportunity_analyses` table; opportunity status becomes `ANALYZED`.

## Database
Run `docker compose exec api alembic upgrade head` after rebuilding.

## Next hardening
Persistent usage ledger, daily spend cap, idempotency for analysis requests,
response evidence verification beyond skill names, and a review/approval workflow.
