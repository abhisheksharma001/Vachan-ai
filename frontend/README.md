# Vachan.ai — Frontend (Phase 0 shell)

Next.js (App Router) + TypeScript. This is the **design-system shell** only —
the Sandy + Coral visual language from [`docs/06_UIUX_DESIGN.md`](../docs/06_UIUX_DESIGN.md):
design tokens, fonts, and the base components (Button, Card, Chat bubble).

The **live Mirror** (chat wired to the backend `/messages` pipeline, plus the
Fidelity Ring and Tonality Sliders) is **Phase 1** — see doc 06 §6.6 #3. This
phase deliberately stops at the shell.

## What's here
- **Tokens** (`app/globals.css`) — the exact §6.2 palette/shadows/radii as CSS
  variables. No hardcoded hex anywhere.
- **Fonts** (`app/layout.tsx`) — Fraunces (display) + Inter (body) + JetBrains
  Mono, self-hosted via `next/font`.
- **Components** (`components/`) — `Button` (3 variants + states), `Card`,
  `ChatBubble` + `TypingBubble`.
- **Showcase** (`app/page.tsx`) — hero, the live palette, the component gallery,
  and a static Mirror preview that shows the **real** PII redaction
  (`+91 …` → `[IN_PHONE]`) the backend performs.

## Run it
```bash
cd frontend
npm install          # one-time
npm run dev          # → http://localhost:3000
```
Production build / typecheck:
```bash
npm run build
```

## Stack choice (Phase 0)
Plain CSS variables + CSS Modules — zero Tailwind/PostCSS config to get wrong,
and the tokens live in one file exactly as doc 06 requires. When we build the
full component library in Phase 1 we can layer in Tailwind + shadcn/ui (doc 06
§6.9) on top of these same tokens.
