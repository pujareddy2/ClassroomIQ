# ClassroomIQ Frontend Foundation

## Architecture

The React/Vite application lives in `frontend/src` and is intentionally a reusable application shell, not a feature dashboard. Its principal boundaries are:

- `app/` — Router and shared application shell.
- `layout/` — responsive navigation, sticky header, footer, global search, and notifications.
- `components/` — small reusable UI primitives (`Button`, `Card`, `Skeleton`, `EmptyState`).
- `services/api/` — Axios instance and API-envelope helpers; components do not own HTTP configuration.
- `store/` — persisted Zustand UI state (theme, sidebar, overlays, notifications).
- `types/` — shared API and notification contracts.
- `styles/` — semantic token system and global accessibility defaults.

Feature routes are placeholders by design. Future module implementations should add their data hooks under `services/` and compose the shared `AppShell`; they should not recreate navigation, headers, footer, providers, or visual tokens.

## Design system

The 8px-based system uses semantic CSS variables, mapped into Tailwind names (`canvas`, `surface`, `ink`, `line`, `brand`, `success`, `warning`, `danger`, `info`). This prevents hard-coded component colors and supports light, dark, and system themes. Typography uses Inter with Manrope fallback. Cards are rounded, low-elevation, and deliberately restrained.

## Responsive strategy

- Desktop: persistent collapsible sidebar.
- Tablet/mobile: off-canvas, keyboard-accessible drawer.
- Main content: fluid constrained container with responsive gutters.
- Cards: single-column mobile and multi-column desktop grid.
- Overlays: full-width safe modal/drawer behavior on narrow screens.
- Tables/charts: future shared components must use horizontally-contained wrappers and Recharts `ResponsiveContainer`.

## Accessibility

- Semantic navigation, buttons, dialog roles, labels, and explicit close controls.
- Visible keyboard focus rings and Ctrl/Cmd+K search shortcut.
- Minimum 40px interactive control height.
- Theme-safe semantic colors and text-first status indicators.
- Motion is limited to short layout/overlay transitions; future components should respect `prefers-reduced-motion` for intensive animation.

## API integration

`services/api/client.ts` targets `VITE_API_URL` or `http://127.0.0.1:8001/api/v1`, attaches a bearer token if present, and creates a request correlation ID. It expects the standardized backend response envelope and exposes `unwrap<T>()` to keep page components clean.

## Verification and performance

`npm.cmd run build` completed successfully with Vite production output. The initial JavaScript bundle is 484.89 kB (155.77 kB gzip); this is acceptable for a foundation but should be code-split by feature route before dashboard/chart modules are implemented. `npm audit` could not reach the registry advisory endpoint in this environment, so its result is not a security clearance.

Run locally:

```powershell
cd frontend
npm.cmd run dev
```

Then verify at 320px, 768px, 1024px, and 1440px widths; test light/dark themes, Ctrl/Cmd+K, drawer close behavior, Tab navigation, and the notification panel.
