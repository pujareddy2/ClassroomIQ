# Manual API Testing Guide

1. Start PostgreSQL and apply the project’s Alembic migrations.
2. Set `DATABASE_URL`, `SECRET_KEY`, and `CORS_ALLOWED_ORIGINS`; start Uvicorn from `backend`.
3. Open `/docs`; confirm every v1 operation has a standard response and error section.
4. Register/login and capture the bearer token. Exercise each canonical POST, then its related GET routes.
5. For each response, check `status`, `message`, `data`, and all metadata fields. Repeat with `X-Request-ID: manual-001` and confirm the same value is returned.
6. Send malformed UUIDs and missing required fields; confirm a 422 `ERROR` envelope. Request a random UUID; confirm a 404 `ERROR` envelope.
7. Repeat an analysis/generation request to confirm module-specific duplicate/idempotency behavior, then verify the matching SQL queries in `DATABASE_VERIFICATION.md`.
8. Upload a file just below and just over `MAX_UPLOAD_SIZE_MB`; verify 201 and 413 respectively. Verify unsupported media types return 415.
9. Use a load tool (for example k6) with independent lecture IDs to test concurrent POSTs. Capture p50/p95 latency, 5xx rate, PostgreSQL pool utilization, and duplicate rows.

Do not interpret a local SQLite/test run as a PostgreSQL performance certification. Execute the load and concurrency steps on a staging PostgreSQL deployment with production-like indexes and connection limits.
