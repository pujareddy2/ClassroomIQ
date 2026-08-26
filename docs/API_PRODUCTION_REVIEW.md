# ClassroomIQ REST API Production Review

## Scope and route inventory

The public API is versioned at `/api/v1`. Registered domains are Authentication, Curriculum, Reference Material, Transcript Intelligence, Technical Validation, Curriculum Coverage, Teaching Intelligence, Recommendation Engine, and Explainable AI.

Canonical write routes are:

| Domain | Canonical route | Persistence target |
| --- | --- | --- |
| Authentication | `POST /auth/register`, `POST /auth/login` | `users` |
| Curriculum | `POST /curriculum/upload` | `curricula`, `topics` |
| Reference Material | `POST /reference/upload` | `reference_materials`, `topic_references` |
| Transcript | `POST /lecture/upload-transcript` | `transcripts`, `transcript_chunks`, `transcript_topic_mappings` |
| Validation | `POST /validation/analyze` | `validation_results`, `validation_summaries`, `validation_evidence` |
| Coverage | `POST /coverage/analyze` | `coverage_results`, `coverage_details`, `coverage_summaries`, `coverage_timelines` |
| Teaching | `POST /teaching/analyze` | teaching intelligence records |
| Recommendations | `POST /recommendations/generate` | recommendations and evidence |
| Explainable AI | `POST /explanations/generate` | explanation, evidence, confidence, citation, reasoning, and decision records |

The legacy `backend/app/api/lecture.py` router is deliberately **not registered** because it duplicates the transcript domain’s resource routes. The redundant `GET /coverage/{lecture_id}` alias was removed; use `GET /coverage/{lecture_id}/summary`. The registered transcript write route remains `POST /lecture/upload-transcript`, matching the public contract requested for this project. No duplicate public operation IDs are registered.

## Standard contract

Every JSON response from `/api/v1`, `/`, and `/health` is normalized at the HTTP boundary:

```json
{
  "status": "SUCCESS",
  "message": "Request completed.",
  "data": {},
  "metadata": {
    "timestamp": "2026-08-05T00:00:00Z",
    "execution_time": 12.34,
    "request_id": "uuid",
    "api_version": "v1"
  }
}
```

Errors use `status: "ERROR"`, `message`, `error.code`, `error.details`, and the same `metadata`. Send `X-Request-ID` to correlate browser, API, and server logs; it is echoed in the response.

## OpenAPI verification

`/docs`, `/redoc`, and `/openapi.json` are enabled. OpenAPI adds the standard success and error envelopes to every v1 operation, documents common error statuses (400, 401, 403, 404, 409, 413, 415, 422, and 500), and supplies a response example. Existing route summaries/descriptions are preserved and augmented with correlation guidance.

Request body schemas are generated from Pydantic models. Multipart upload endpoints document their form fields and file field. The application should generate its OpenAPI schema once at startup/deployment and publish it as the frontend contract.

## Automated verification

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

The suite exercises domain services plus HTTP success paths, validation failures, missing records, duplicate analysis behavior, persistence paths, and the new response/OpenAPI contract. The API contract tests are in `backend/tests/test_api_contract.py`.

## Production readiness checklist

- [x] Versioned public routes and canonical names
- [x] HTTP status codes and consistent JSON envelope at the boundary
- [x] Request correlation IDs, timing metadata, and request logging
- [x] Pydantic request validation and uniform 422 errors
- [x] Database session rollback/close lifecycle
- [x] Database-backed service/repository reads and explicit POST commits
- [x] Pagination limits for list endpoints that expose paging
- [x] CORS is allow-list based via `CORS_ALLOWED_ORIGINS`
- [x] Swagger/ReDoc schema documents standard responses and errors
- [x] JWT authentication required for all non-auth v1 routes
- [ ] Add object-level ownership checks (faculty/institution tenancy) before multi-tenant production
- [ ] Configure centralized structured log sink, metrics/tracing, rate limiting, and upload malware scanning
- [ ] Run against a dedicated PostgreSQL staging database with Alembic migrations, load, and concurrency tests

The unchecked items are deployment controls, not safe to infer or enable without the frontend token migration and tenancy policy. They must be completed before an unconditional internet-facing production launch.
