# Frontend–Backend Integration Report

## Implemented connectivity

The SPA uses the FastAPI v1 envelope through one Axios client (`VITE_API_URL`, default `http://127.0.0.1:8001/api/v1`). It attaches bearer credentials and an `X-Request-ID` to every request. TanStack Query owns server data and retries only transient failures; Zustand owns only session/UI/context state.

| Frontend route | Live FastAPI calls |
| --- | --- |
| `/login` | `POST /auth/login`; guarded routes verify `GET /auth/me` |
| `/curriculum` | `GET /curriculum` |
| `/lectures` | `GET /lecture/{id}`, `/chunks`, `/mappings`, `/statistics` |
| `/coverage` | summary, topics, remaining, timeline |
| `/validation` | results, summary, evidence, timeline |
| `/teaching` | summary, strengths, weaknesses, interaction, structure |
| `/recommendations` | list, priority, evidence |
| `/explainability` | package, summary, evidence, transcripts, citations, confidence, reasoning |
| `/dashboard` | lecture, coverage, validation, teaching, and recommendation summaries |
| `/profile` | `GET /auth/me` |

All lecture intelligence views use the globally persisted `selectedLectureId`; changing it rekeys the React Query cache and refreshes every dependent route automatically.

## Intentional unavailable states

The current FastAPI route registry has **no** analytics, reports, notifications, or list-lectures APIs. `/analytics` and `/reports` therefore present an explicit API-unavailable state rather than mock data. The notification center is prepared in Zustand but has no fabricated messages. Add backend routers before claiming these domains are live.

## Authentication and navigation

`ProtectedRoute` redirects users without a token to `/login`, validates stored sessions through `/auth/me`, and clears invalid sessions. Every sidebar route resolves to a concrete route and preserves the shared application shell. The active navigation item is supplied by `NavLink`.

## Verification

`npm.cmd run build` passes with strict TypeScript and Vite production build. Verify manually by running `npm.cmd run dev`, signing in with a valid backend user, selecting a persisted lecture UUID, and checking each relevant route. Test unauthenticated redirects, a nonexistent UUID (404), malformed input (422), expired token (401), mobile drawer navigation, Ctrl/Cmd+K, and light/dark mode.
