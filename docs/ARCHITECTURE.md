# Architecture decision record — Foundation

- Modular monolith: FastAPI API, future independent collector/worker/bot processes.
- PostgreSQL is the source of truth. Unique `(source_id, external_id)` prevents duplicate imports.
- Alembic manages schema changes; no `create_all()` on application startup.
- External source content is untrusted and must not control tools, secrets or outbound actions.
- No source polling or AI requests are implemented in this phase.
- Manual approval is mandatory before any future proposal submission.
- No public admin endpoints: API is bound to localhost in Compose, admin routes use an explicit token.
- Source-specific collection is disabled until permission and terms have been checked.

## Future work

Add database-backed processing queue, source policy registry, portfolio, analysis, Telegram bot,
proposal workflow and backup/restore procedures in subsequent blocks.
