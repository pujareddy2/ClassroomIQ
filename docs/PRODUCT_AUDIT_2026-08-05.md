# ClassroomIQ product audit

## Working

- Authentication, protected routing, curriculum upload/listing, reference upload, transcript upload and lecture reads.
- Central analysis job API (`POST /analysis/run`, `GET /analysis/status/{lecture_id}`) and read-only analysis result pages.
- Shared response envelope, auth redirect, API request IDs, error boundaries, dark/light theme toggle and responsive navigation.

## Partially working

- Dashboard shows selected-context and workflow information but has no primary analysis action or recent activity feed.
- Notifications are browser-local; upload events populate them, but there is no persisted notification API.
- Search is a static list, not a search of stored classroom data.
- Profile page reads the authenticated user; its header avatar has no menu.
- Settings are local browser preferences only.
- Assistant UI accepts prompts but the returned service response is not rendered; it is not yet lecture-data constrained.

## Broken or misleading

- Reports and Analytics deliberately render unavailable placeholders, because no API routers are registered.
- Reference Materials claims its library endpoint is unavailable, despite the product requiring document management.
- AI pages correctly wait for the central job, but a failed/pending job must be surfaced as terminal state rather than an unbounded spinner.

## Missing backend APIs

- Aggregated lecture insight/report data for dashboard, report generation and analytics.
- Persisted notification, support-ticket and preference resources.
- Global cross-domain search and reference-material listing/management.
- Report-file generation/export and recommendation workflow-state mutations.

## Dead/unused code and API calls

- `analytics-service.ts` and `report-service.ts` only reject intentionally and are placeholder implementations.
- The old frontend analysis orchestrator was removed; the central analysis status endpoint is the sole poll target.
- `backend/app/api/lecture.py` is present but not registered in `main.py`; transcript router supplies the active lecture endpoints.

## Implementation priority

1. Keep one analysis-run action and make result pages viewers only.
2. Add database-backed insight aggregates for dashboard, reports and analytics.
3. Wire profile menu, assistant result rendering and non-deceptive empty/error states.
4. Add persisted notifications, settings, support and search as separate API resources rather than inventing browser-only records.
