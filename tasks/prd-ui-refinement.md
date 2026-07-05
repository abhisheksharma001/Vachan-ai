# UI Refinement — Vachan.ai Frontend

## Intro

A pass across the entire frontend (Next.js 14 + Tailwind v4 + shadcn/ui) to
fix concrete, verified inconsistencies and gaps rather than introduce a new
visual language. Direction: refine the existing Sandy + Coral design system,
don't replace it.

Every item below was verified against the actual codebase before being
written down — no speculative "best practices" filler.

## Verified Findings

1. **No accessibility skip link.** `app/(app)/layout.tsx` has a `<main>`
   landmark but no "Skip to main content" link — keyboard/screen-reader users
   must tab through the full sidebar nav on every page load.
2. **Orphaned `app/theme.css`.** Defines a full duplicate `@theme` token
   block (colors) that nothing imports. The live tokens are in
   `app/globals.css` (imported by `app/layout.tsx`). Dead file, safe to
   delete.
3. **No motion/duration design tokens.** `globals.css` defines color/radius
   tokens but zero `--duration-*` tokens. Components hardcode raw numerals
   instead: `duration-100` (dialog.tsx, dropdown-menu.tsx), `duration-200`
   (AppSidebar.tsx), `duration-500` (FidelityRing.tsx).
4. **Confirmed-orphaned components.** `PersonaList.tsx`, `QuickActions.tsx`,
   `FidelityRingMini.tsx` in `components/vachan/` have zero importers anywhere
   in `app/` or `components/` (verified via grep). Dead code from a prior
   dashboard iteration.
5. **`/settings` is an empty shell.** `app/(app)/settings/page.tsx` is just a
   static heading + one paragraph, no real content.
6. **`/channels` is unreachable and stylistically orphaned.** It's not in
   `AppSidebar`'s nav list at all (only reachable by typing the URL). It
   lives outside the `(app)` route group, uses its own CSS Modules file
   instead of Tailwind/shadcn, and hand-rolls its own nav bar that only links
   to `/dashboard` and `/mirror` (missing itself, Personas, Conversations,
   Settings).
7. **Hardcoded one-off hex colors bypassing the token system.**
   `FidelityRing.tsx`'s SVG gradient stops use raw hex (`#F3C9A8`,
   `#EC6A4C`) instead of the design tokens — one of them doesn't even match
   its nearest existing token exactly (a silent color drift).

## Goals

- Fix all 7 verified findings above.
- Do not introduce a new design language — extend the existing token system
  (colors, motion) so these fixes are consistent with it.
- Do not invent new backend functionality — `/settings` and `/channels` use
  only data/hooks that already exist in the codebase.
- Finish with a manual visual QA pass across every real page (marketing +
  core app) to catch anything a static audit missed.

## Non-Goals

- No new design system / visual rebrand.
- No new backend endpoints or database changes.
- No dependency upgrades (Next.js 14 stays as-is; that's a separate,
  larger, already-tracked effort).
- No auth/login UI — none exists yet (dev-mode auto-token architecture);
  out of scope until a real login flow is built.

## User Stories

### US-001 — Add a skip-to-content link
As a keyboard/screen-reader user, I want to skip the sidebar nav and jump
straight to page content, so I don't have to tab through navigation on every
page.
- Add a visually-hidden-until-focused "Skip to main content" link as the
  first focusable element in `app/(app)/layout.tsx`.
- Give the `<main>` element `id="main-content"` and `tabIndex={-1}`.
- Activating the link moves focus to `<main>`.

### US-002 — Delete the orphaned `app/theme.css`
As a maintainer, I want dead duplicate token definitions removed, so there's
one source of truth for the design system.
- Delete `app/theme.css` after confirming (again) nothing imports it.
- `globals.css` remains the sole token source; visual output unchanged.

### US-003 — Add motion/duration design tokens
As a maintainer, I want duration values defined once as tokens, so
components stop hardcoding raw numerals.
- Add `--duration-fast: 100ms`, `--duration-base: 200ms`,
  `--duration-slow: 500ms` to `globals.css`'s `@theme` block (matching the
  exact values already in use, so nothing visually shifts).
- Migrate `dialog.tsx`, `dropdown-menu.tsx` (100ms), `AppSidebar.tsx`
  (200ms), and `FidelityRing.tsx` (500ms) to the new token-based utility
  classes instead of raw numerals.

### US-004 — Delete confirmed-orphaned components
As a maintainer, I want dead code removed, so the component directory
reflects what's actually used.
- Delete `components/vachan/PersonaList.tsx`, `QuickActions.tsx`,
  `FidelityRingMini.tsx`.
- Re-confirm zero importers before deleting (grep across `app/` and
  `components/`).

### US-005 — Give `/settings` real content
As a user, I want the Settings page to show something useful instead of a
placeholder, so it's not a dead end.
- Use existing data only: the persona list (via the existing
  `usePersonas` hook and `PersonaCard`/`EmptyState` components already used
  elsewhere) and a simple account/identity section.
- No new backend calls or endpoints — reuse what other pages already fetch.
- Matches the app's existing layout/token system (already inherits
  `AppSidebar` via the `(app)` layout).

### US-006 — Bring `/channels` into the shared layout and navigation
As a user, I want to reach the Channels page from the sidebar like every
other page, and have it look consistent with the rest of the app.
- Move the route into the `(app)` route group so it inherits `AppSidebar`
  and the shared layout automatically.
- Add a "Channels" entry to `AppSidebar`'s `NAV` array.
- Remove the page's own hand-rolled nav bar and its CSS Modules file;
  restyle its content (`ChannelStatusGrid`, export cards) with the existing
  Tailwind/shadcn tokens (sand/coral/ink) instead of custom CSS classes.
- Existing content (channel list, export options) is preserved, just
  restyled and properly reachable.

### US-007 — Tokenize `FidelityRing`'s hardcoded gradient colors
As a maintainer, I want the fidelity ring's gradient built from design
tokens, not magic hex strings, so the color system has one source of truth.
- Replace the two hardcoded hex stops with references to CSS custom
  properties. Add a `--color-coral-200` token (matching the existing
  `#F3C9A8` value, fitting the existing coral-300/400/500 scale) rather than
  silently snapping to the nearest existing token and shifting the visual.
- Visual appearance is pixel-identical before/after.

### US-008 — Final cross-app visual QA pass
As a maintainer, I want to confirm nothing regressed across the whole app
after the above changes.
- Walk through: marketing home, marketing open-source page, dashboard,
  personas list + detail, conversations list + detail, mirror, settings,
  channels.
- Screenshot each; fix any real visual regression found (not hypothetical
  ones).
- This is the story that closes out the "Everything" scope — if it finds
  nothing else broken, that's a valid, honest outcome.

## Acceptance Criteria (all stories)

Every story additionally requires:
- `cd frontend && npm run build` passes (this project's typecheck — `next
  build` type-checks the whole program).
- `cd frontend && npm run lint` passes.
- UI-affecting stories verified in an actual browser (dev-browser skill or
  equivalent), not just code-reviewed.
