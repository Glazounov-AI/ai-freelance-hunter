# Block B — manual opportunity intake

Only user-supplied order data is accepted. No website polling, scraping, private API
access or automated proposals are enabled. FL.ru, Kwork and Freelance.ru are blocked
in the source policy registry until explicit legal/technical review.

Authenticated endpoints (`X-Admin-Token`):
- `POST /api/v1/opportunities/manual` — manual ingestion; optional `external_id`
  is the idempotency key. Reusing it returns the existing record with `created=false`.
- `GET /api/v1/opportunities?limit=50&offset=0&status=new`
- `GET /api/v1/opportunities/{id}`

Without an `external_id`, each POST creates a new opportunity. This is intentional:
identical titles/descriptions do not necessarily refer to the same order.
Records are never overwritten on duplicate submissions.

All endpoints remain accessible only on the configured localhost-bound API port.
