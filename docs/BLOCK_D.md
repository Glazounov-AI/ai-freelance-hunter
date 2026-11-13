# Block D — human-reviewed applications

API uses the existing `X-Admin-Token` header.

1. `POST /api/v1/applications` with `{"analysis_id": 1}` creates one draft per opportunity.
2. `GET /api/v1/applications` lists drafts (supports `status`, `limit`, `offset`).
3. `GET /api/v1/applications/{id}` reads one draft.
4. `PATCH /api/v1/applications/{id}/draft` with `{"draft": "..."}` edits a pending draft.
5. `POST /api/v1/applications/{id}/approve` with `{"note": "Reviewed"}` approves.
6. `POST /api/v1/applications/{id}/reject` with `{"note": "Not a fit"}` rejects.
7. `GET /api/v1/applications/{id}/history` shows an append-only application event log through the API.

Only drafts may be edited, approved, or rejected. Approval does **not** send anything to a platform. The database has a unique constraint on `opportunity_id` to prevent duplicate application records. Requests for an already processed opportunity return 409.

Migrate using the project's normal Alembic workflow (`alembic upgrade head`). Never run downgrade against production data without a backup.

## Limitations

The event history records actions and notes but not the full text of every previous draft version. There is one shared admin token, so it cannot identify which human reviewer acted. This block does not include platform connectors, send state, background workers, or automatic dispatch.
