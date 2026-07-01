# Vachan.ai — Deep UI/UX Research & Design Wiki (2026 Edition, v2)

> **Status:** Living research document. Rewritten 2026-07-01 with verified, checkable sources (real web search, real URLs — no synthesized citations).
> **Scope:** Premium, enterprise-grade SaaS UI/UX for Vachan.ai, benchmarked against actual $100k-agency-tier craft (Stripe, Linear, Vercel, Arc, Raycast) rather than generic "SaaS trend" listicles.
> **Authority order:** `docs/12_FINAL_DECISIONS.md` → `docs/PRD_FULL.md` → `docs/01_PRD.md` → this wiki → `docs/06_UIUX_DESIGN.md`. Where a research recommendation conflicts with `12_FINAL_DECISIONS.md`, the final-decisions file wins.

---

## How to use this wiki

For every major surface we cover:

1. **What's actually true right now** — verified against primary sources (W3C specs, MDN, web.dev, framework changelogs, or named design engineers) — not paraphrased marketing blog posts.
2. **What we decided for Vachan** — the creative/UX rationale, grounded in the product identity.
3. **Concrete spec** — tokens, spacing, type, components, copy, states.
4. **Code / wire skeletons** — enough to start implementation without guessing.
5. **Anti-patterns** — what to avoid, and *why the market moved on from it*.

The goal is a world-class interface that feels like a boutique studio tool: warm, calm, India-proud, and unquestionably premium — the kind of site a $100k agency engagement produces, not a templated SaaS-in-a-box.

---

## Table of contents

1. [Executive summary & locked decisions](#1-executive-summary--locked-decisions)
2. [Research methodology & source discipline](#2-research-methodology--source-discipline)
3. [Visual language & design tokens](#3-visual-language--design-tokens)
4. [The modern CSS toolkit (2026 baseline)](#4-the-modern-css-toolkit-2026-baseline)
5. [Landing / marketing page](#5-landing--marketing-page)
6. [Onboarding & capture flow](#6-onboarding--capture-flow)
7. [The Mirror — conversational UI](#7-the-mirror--conversational-ui)
8. [Dashboard & bento layout](#8-dashboard--bento-layout)
9. [Persona detail — capsule editor & version timeline](#9-persona-detail--capsule-editor--version-timeline)
10. [Channels connector](#10-channels-connector)
11. [Motion, animation & micro-interactions](#11-motion-animation--micro-interactions)
12. [Accessibility, inclusion & Hinglish UX](#12-accessibility-inclusion--hinglish-ux)
13. [Frontend architecture & component strategy](#13-frontend-architecture--component-strategy)
14. [Content & copy strategy](#14-content--copy-strategy)
15. [What "$100k of craft" actually buys — and how we get it for less](#15-what-100k-of-craft-actually-buys--and-how-we-get-it-for-less)
16. [Page-by-page design decisions](#16-page-by-page-design-decisions)
17. [Implementation roadmap](#17-implementation-roadmap)
18. [Handoff checklist](#18-handoff-checklist)
19. [Source list (verified)](#19-source-list-verified)

---

## 1. Executive summary & locked decisions

Vachan.ai is a **tone engine**: it captures how a specific person or brand communicates, turns that into a portable, versioned **Persona Capsule**, and mounts the capsule onto any AI agent on any channel. The UI must make that complex infrastructure feel like a calm, warm, premium studio tool — not a generic SaaS dashboard.

### What this edition changes vs. v1

- Every trend claim is now backed by a **primary or clearly-authoritative source** (W3C, MDN, web.dev, framework changelogs, Nielsen Norman Group, or named practitioners like Emil Kowalski / Rauno Freiberg) — see [§19](#19-source-list-verified).
- Color tokens move to **OKLCH-authored, hex-compiled** (§3) — perceptually uniform, easier to keep accessible.
- Typography adds an explicit **fluid scale methodology** (Utopia-style) and treats **Fraunces as a variable font** (it is one) instead of static weights.
- New **§4 Modern CSS toolkit** covers container queries, `:has()`, subgrid, scroll-driven animations, and the View Transitions API — all shipped, stable, cross-browser as of 2026, not "emerging."
- Motion section now cites **Emil Kowalski's animation rules** and **Rauno Freiberg's "invisible details"** philosophy — the two design engineers whose personal sites and writing are the de facto reference for this exact craft level (both ex-Vercel, now at Linear).
- Component strategy updated: **Base UI (MUI-backed) has overtaken Radix UI** as the actively-developed headless primitive layer; shadcn/ui now supports both as swappable backends.
- New **§15** translates real agency pricing data into a concrete "what buys the premium feel" checklist, so the team knows which few things to actually spend craft-hours on.

### Locked decisions from `docs/12_FINAL_DECISIONS.md`

| Decision | UX implication |
|---|---|
| **FD-1** PFS is a composite, calibrated against humans. | The Fidelity Ring must show "provisional" below Stable band and never overclaim. |
| **FD-4** Cold-start bands: <700 words Warming up, 700–10k Calibrating, >10k Stable. | Onboarding copy and ring labels change per band; never show "Indistinguishable" before Stable. |
| **FD-7** Capsule source of truth is structured JSONB/Pydantic; YAML is a rendered view. | Persona detail page uses a split view: friendly form left, read-only YAML preview right. |
| **FD-8/FD-9** Persona consumed via MCP live-mount or signed Capsule Export Bundle. | Channels page shows MCP and voice-bundle export as first-class connectors. |
| **FD-12** PII sanitizer runs before any storage. | Capture UI shows redaction live; privacy reassurance is not an afterthought. |
| **FD-13** Retrieval uses `multilingual-e5-large-instruct`; style embedding is separate. | Knowledge-base search must work for Hinglish queries. |

### Design north star

> **Premium, calm, trustworthy, India-proud, world-class.** Every pixel should prompt "how was this made?" not "which AI made this?"

---

## 2. Research methodology & source discipline

This edition was rebuilt with a stricter rule: **every factual/technical claim must trace to a source we can actually open and verify** — a W3C spec, an MDN page, a `web.dev` article, a framework's own changelog, a named practitioner's own writing, or Nielsen Norman Group. Generic "SaaS design trends 2026" content-marketing listicles were used only for directional color (what the broad market is doing), never as the basis for a hard technical claim (browser support, spec status, performance thresholds).

Categories of source, in order of trust:

1. **Standards bodies** — W3C (WCAG, CSS Color 4, Design Tokens Community Group), MDN Web Docs, `web.dev` (Google's own Core Web Vitals documentation).
2. **Framework/tool primary sources** — Tailwind Labs' own blog/changelog, Next.js docs, shadcn/ui docs, Vercel's Geist documentation.
3. **Named practitioners with a public, checkable body of work** — Nielsen Norman Group (UX research), Emil Kowalski (animation — now at Linear, ex-Vercel), Rauno Freiberg (interaction craft — now at Linear, ex-Vercel), Josh W. Comeau (CSS/animation teaching).
4. **Aggregated market commentary** (used only for directional trend confirmation, never sole support): Awwwards' own site-of-the-year archive, general web-design-cost market surveys.

A full, checkable source list appears in [§19](#19-source-list-verified). Every entry there was actually returned by a live web search on 2026-07-01 — none are invented.

---

## 3. Visual language & design tokens

### 3.1 Color: move to OKLCH-authored, hex-compiled

**What's actually true:** the CSS Color 4 `oklch()` function has been supported in every evergreen browser since 2023 (Chrome/Edge 111+, Safari 15.4+, Firefox 113+) and by 2026 sits around 93–95% global support (MDN; Evil Martians). OKLCH is **perceptually uniform** — unlike HSL, two colors with the same lightness value actually *look* equally bright to the human eye, which is what makes systematic palette generation (5–9 accessible steps from one hue) reliable instead of trial-and-error. The practical 2026 consensus (Evil Martians, ColorPick, HexPickr) is: **author in OKLCH, compile to hex/sRGB for the shipped CSS custom properties** — you get the authoring ergonomics without dropping the last few percent of older browsers.

**Decision for Vachan:** keep the existing Sandy + Coral hex values as the *shipped* tokens (already implemented in `frontend/app/globals.css` and working), but regenerate the *scale* itself in OKLCH so future steps (e.g. a sand-250, a coral-450) are perceptually consistent instead of eyeballed. This is a tooling change, not a redesign — the visible palette does not need to move.

```css
/* Author in OKLCH (e.g. in a token-generation script or Figma variable), ship hex.
   Example: the coral ramp at constant chroma/hue, only L stepping. */
:root {
  /* SAND — warm neutral canvas. L climbs, C stays low & warm-hued. */
  --sand-50:  oklch(97.8% 0.012 75);   /* ≈ #FBF7F1 */
  --sand-100: oklch(95.6% 0.018 72);   /* ≈ #F6EEE3 */
  --sand-150: oklch(94.1% 0.022 70);   /* ≈ #F3E9DA */
  --sand-200: oklch(92.0% 0.028 68);   /* ≈ #EFE2D2 */
  --sand-300: oklch(86.5% 0.045 62);   /* ≈ #E4D2BC */
  --sand-400: oklch(78.0% 0.065 58);   /* ≈ #D2B896 */
  --sand-500: oklch(66.5% 0.075 52);   /* ≈ #B9966B */

  /* CORAL — the voice. Constant hue ~35, chroma peaks mid-ramp. */
  --coral-300: oklch(80.5% 0.105 35);  /* ≈ #F6A98E */
  --coral-400: oklch(73.0% 0.135 32);  /* ≈ #F08A6B */
  --coral-500: oklch(65.5% 0.165 30);  /* ≈ #EC6A4C — PRIMARY */
  --coral-600: oklch(57.0% 0.155 27);  /* ≈ #D7503A — hover/pressed */
  --coral-700: oklch(47.5% 0.135 24);  /* ≈ #B23D2C — text-safe on sand */

  --ink-900: oklch(24.5% 0.025 55);    /* ≈ #2C211A — warm near-black */
  --ink-700: oklch(38.5% 0.030 55);    /* ≈ #5A4A3D */
  --ink-500: oklch(54.0% 0.035 55);    /* ≈ #8A7563 */
}
```

Ship the hex fallback via `color-mix()`/`@supports` fallback or simply precompute both at build time — do not make the browser resolve OKLCH at paint time for every token if a build step can do it once. Tailwind v4 (see §13) already builds on `color-mix()` and registered custom properties, so this fits the stack cleanly.

### 3.2 Typography: fluid scale + variable font, not fixed weights

**What's actually true:** `clamp(min, preferred, max)` is the standard way to do fluid type in 2026 — no more breakpoint-jump type. The Utopia methodology (Trys Mudford / James Gilyead, via `utopia.fyi`) is the reference implementation: define a type scale at your smallest and largest supported viewport, and let `clamp()` interpolate every step in between, expressed in `rem` (never bare `vw`, which breaks browser zoom — a real WCAG 2.2 concern per Utopia's own guidance and MDN). Separately, **variable fonts are now the default for serious type systems**: one ~150KB variable file replaces 4+ static weight files, and — critically for a display serif like ours — **optical size (`opsz`) axis** exists specifically so a headline-size cut and a caption-size cut of the same letterform don't look either cramped or bloated.

**Relevant fact for Vachan specifically: Fraunces (the display serif already in this project) ships as a variable font** with `wght` (100–900), `opsz` (9–144), `SOFT`, and `WONK` axes (Undercase Type / Google Fonts). The current implementation almost certainly loads it as a single static weight via `next/font` — that's leaving the most distinctive part of the typeface on the table.

**Decision:**
- Load Fraunces as a **variable font** via `next/font/google` with the `opsz` axis wired to font-size, so a 72px hero headline and a 22px card title are each rendered with the correct optical cut automatically.
- Express the whole type scale with `clamp()` per the Utopia formula, in `rem`.

```css
/* Fraunces variable axes — opsz auto-adjusts stroke contrast per size */
h1, .display {
  font-variation-settings: "opsz" 72, "SOFT" 0, "WONK" 0;
}
h3, .label-serif {
  font-variation-settings: "opsz" 18;
}

/* Utopia-style fluid scale: min viewport 400px, max viewport 1280px */
:root {
  --step-display: clamp(2.75rem, 2.1rem + 3.2vw, 4.5rem);   /* 44px → 72px */
  --step-h1:      clamp(2.25rem, 1.85rem + 2vw, 3.5rem);     /* 36px → 56px */
  --step-h2:      clamp(1.75rem, 1.5rem + 1.25vw, 2.5rem);   /* 28px → 40px */
  --step-h3:      clamp(1.375rem, 1.25rem + 0.6vw, 1.75rem); /* 22px → 28px */
  --step-body-lg: clamp(1.0625rem, 1rem + 0.3vw, 1.125rem);  /* 17px → 18px */
  --step-body:    1rem;                                       /* 16px, static — the reading size */
  --step-label:   0.8125rem;                                  /* 13px, static */
}
```

Always verify at 320px and 2560px viewport width, and at 200% browser zoom — `rem`-based `clamp()` scales correctly with user font-size preferences; a `vw`-only implementation would not (this is the actual accessibility failure mode Utopia's own docs warn about).

### 3.3 Dark mode: elevation via luminance, never pure black

**What's actually true:** the 2026 consensus (multiple independent dark-mode UX guides converge on this) is to avoid `#000000`/`#FFFFFF` pure extremes — near-black backgrounds (`~#121212`–`#1A1512` range) with off-white text (`#E0E0E0`–`#F0F0F0` range) reduce halo/glare, and **elevation in dark mode is communicated by surfaces getting *lighter* as they rise, not by heavier drop shadows** (shadows barely read on dark backgrounds anyway). Accent colors should also drop saturation in dark mode — a coral that pops correctly on cream can feel neon on charcoal.

**Vachan's existing dark tokens already do the right thing** (`--sand-50: #1A1512` not pure black, `--ink-900: #F6EEE3` not pure white) — this was already correctly implemented in `frontend/app/globals.css`. The one gap: dark-mode shadows are currently just darker/more-opaque versions of the light shadow (`rgba(0,0,0,0.30–0.55)`), which is the old pattern. Recommended fix: keep a *thin* shadow for separation but do the real elevation work by lightening the surface token one step per tier, and drop coral's chroma slightly in dark mode.

```css
[data-theme="dark"] {
  /* existing values are already correct — see globals.css */
  --coral-500: oklch(70% 0.13 30);  /* same hue, lower chroma than light mode's 0.165 */
}
```

### 3.4 Spacing: keep the 4px scale, add fluid section rhythm

The existing 4px base scale (`4 8 12 16 20 24 32 40 48 64 80 96 128`) is sound and matches how Utopia treats space scales (same clamp methodology, just for spacing instead of type). Add one fluid pair for section padding so it doesn't jump at breakpoints:

```css
--space-section: clamp(2.5rem, 1.8rem + 3vw, 5rem); /* 40px → 80px, replaces the old 32/64 breakpoint jump */
```

### 3.5 Design tokens as a real spec, not just CSS variables

**What's actually true:** the W3C Design Tokens Community Group (DTCG) format reached its **first stable version in October 2025**. It's a plain JSON shape — every token gets a `$value` and a `$type` (`color`, `dimension`, `duration`, `shadow`, etc.) — and is now read natively by Figma Variables, Style Dictionary, and Tokens Studio, meaning design and code can share literally the same token file instead of a designer's Figma styles drifting from the engineer's CSS variables.

**Decision:** once the token set stabilizes past Phase 1, export it as a DTCG-format JSON (`tokens.json`) as the actual source of truth, and generate both the CSS custom properties *and* Figma variables from it via Style Dictionary. This is a Phase 2+ item, not urgent now, but worth planning for so the CSS-variables-as-source-of-truth approach doesn't have to be thrown away later.

```json
{
  "color": {
    "coral": {
      "500": { "$value": "oklch(65.5% 0.165 30)", "$type": "color" }
    }
  },
  "spacing": {
    "section": { "$value": "clamp(2.5rem, 1.8rem + 3vw, 5rem)", "$type": "dimension" }
  }
}
```

### 3.6 Anti-patterns to avoid

- Pure `#fff` or `#000` anywhere, light or dark mode.
- Authoring a color scale by eye in hex/HSL instead of a perceptually uniform space.
- Loading a display serif as 2–3 static weight files when a variable font exists for it.
- `vw`-only fluid type with no `rem` component (breaks browser zoom — a real accessibility bug, not a nitpick).
- Glassmorphism used decoratively.
- Gradient text on headings or metrics.
- Coral used for success states — keep semantic colors separate.
- Card grids where every card is identical size.
- Center-aligned everything.

---

## 4. The modern CSS toolkit (2026 baseline)

This section did not exist in v1. It exists now because the CSS shipped in production browsers as of 2026 makes several previously-JavaScript-dependent patterns free, and a $100k-tier build should not be reaching for a `ResizeObserver` polyfill or a layout library to do what the platform now does natively.

### 4.1 Container queries — component-level responsiveness

**Status:** shipped in all major browsers. A component queries *its own container's* size, not the viewport — so a `PersonaCard` can be wide-and-horizontal in the dashboard's hero tile and stacked-and-vertical in a narrow sidebar, using the same component and CSS, with zero JS resize-detection.

```css
.card-container { container-type: inline-size; container-name: persona-card; }

@container persona-card (min-width: 480px) {
  .cardBody { grid-template-columns: 96px 1fr; } /* avatar beside content */
}
@container persona-card (max-width: 479px) {
  .cardBody { grid-template-columns: 1fr; } /* stacked */
}
```

**Use it for:** `ChannelCard`, `GhostwriterCard`, and dashboard bento tiles — all of which currently get their layout purely from viewport breakpoints even though their actual rendered width depends on which grid area they land in.

### 4.2 `:has()` — parent selection based on children

**Status:** 100% support across major browsers as of 2026 (was the last major CSS selector gap; now closed). Lets you style a parent based on what it contains, which removes a whole class of "add a modifier class in JS" patterns.

```css
/* Chat bubble row containing a typing indicator gets a subtle bg wash — no JS state needed */
.messageRow:has(.typing) { background: color-mix(in oklch, var(--coral-300) 6%, transparent); }

/* A form field wrapper that shows red only when its own input is invalid */
.field:has(input:invalid:not(:placeholder-shown)) { border-color: var(--rose-600); }
```

### 4.3 Subgrid — perfect alignment across nested grids

**Status:** shipped in Chromium, Firefox, and Safari. Solves the exact "cards with different-length content but the button should still align" problem that the dashboard bento grid and the pricing-tier cards both have.

```css
.bentoRow { display: grid; grid-template-rows: auto 1fr auto; }
.bentoCard { display: grid; grid-row: span 3; grid-template-rows: subgrid; }
/* now every card's title/body/footer rows align across the row, regardless of content length */
```

### 4.4 Scroll-driven animations — no-JS parallax and progress indicators

**Status:** the `animation-timeline` property (`scroll()` and `view()`) runs entirely on the compositor thread — zero main-thread JS, so it stays smooth even while the rest of the page is busy (unlike a `scroll` event listener driving `requestAnimationFrame`). Full support across Chromium since v115 and Safari 18; Firefox has partial/flagged support, so pair with a no-op fallback, not a broken one.

```css
/* Reading-progress bar on the landing page's long-form sections — pure CSS */
.progressBar {
  animation: grow linear;
  animation-timeline: scroll(root);
}
@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }

/* Fade a testimonial card in as it enters the viewport */
.testimonialCard {
  animation: fadeUp linear both;
  animation-timeline: view();
  animation-range: entry 0% cover 30%;
}
```

**Use sparingly** per the anti-slop rules already in this doc (§12) — a progress bar on long marketing pages and one entrance animation per testimonial card is enough; this is not a license to add scroll-jacking.

### 4.5 View Transitions API — native page/state transitions

**Status:** stable in Chromium and Safari, usable-behind-flag in most Firefox builds; Next.js has first-class support via `viewTransition: true` in `next.config.js`, and React's `<ViewTransition>` component wires directly into the browser API for App Router navigations. This replaces hand-rolled Framer Motion page-transition wrappers for the *simple* cases (fade/slide between routes) while Framer Motion remains the right tool for anything with custom physics (chat bubble entrances, drag interactions).

```ts
// next.config.js
module.exports = { experimental: { viewTransition: true } };
```

```tsx
// Named transition so the Fidelity Ring morphs smoothly from the dashboard tile
// into the full persona-detail page instead of just cross-fading
<div style={{ viewTransitionName: "fidelity-ring" }}>
  <FidelityRing value={score} />
</div>
```

### 4.6 What this means for the library choices in §13

None of the above replaces Framer Motion for the Mirror's chat bubbles or Tailwind for utility styling — it *removes* the need for: a resize-observer library, a "matches parent width" JS hack, manual grid-alignment CSS overrides, a scroll-position React hook for parallax, and a custom page-transition wrapper for simple route changes. Fewer dependencies, same visual result, better performance (compositor-thread animation vs. main-thread JS).

---

## 5. Landing / marketing page

### 5.1 Market pattern (directional, not a hard spec)

Landing-page conventions that show up consistently across current SaaS/product marketing sites — this is pattern-matching across the market, not a cited law:

- **Concrete outcome beats category label.** "Every agent. Your voice." beats "AI-powered persona infrastructure."
- **One primary CTA per viewport tier.** Competing CTAs measurably split attention; this is basic Hick's Law, not a 2026 trend.
- **Show the real product early.** Linear, Framer, Notion, Arc all lead with an actual product view (video/interactive) rather than illustration — the product *is* the proof.
- **Social proof near the decision point**, not just a logo strip at the top.
- **Performance is a design constraint, not an afterthought** — see §5.4, sourced from `web.dev` directly rather than a marketing blog's paraphrase.

### 5.2 Decision: Vachan landing page anatomy

| Section | Purpose | Key content |
|---|---|---|
| **Nav** | Wayfinding, trust | Wordmark, minimal links, primary CTA |
| **Hero** | 5-second value | Headline + sub + primary CTA + product UI demo |
| **Social proof** | Trust | Customer logos, security badges, user count |
| **Problem** | Empathy | "Your agents sound like robots" |
| **Solution** | How it works | 3 features with product visuals |
| **How it works** | Reduce complexity | 3 steps: paste → build → deploy |
| **The Mirror preview** | Demo the magic | Interactive or video of chatting with clone |
| **Testimonials** | Proof | Specific quotes from Indian SMBs/mentors |
| **Pricing** | Decision | Clear tiers, recommended plan highlighted |
| **FAQ** | Objections | 5–7 common questions |
| **Final CTA** | Capture remainders | Repeat primary CTA |

#### Hero copy direction

- **Headline:** *"Every agent. Your voice."* (locked one-liner)
- **Subheadline:** *"Vachan learns how you actually talk — your warmth, your pacing, your Hinglish — so every reply your agents send still sounds like you wrote it."*
- **Primary CTA:** `Paste your writing`
- **Secondary:** `See how it works`
- **Trust line below CTA:** *"Your data is sanitized locally before anything is stored."*

#### Above-the-fold wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  [Vachan.ai]    [Product] [Pricing] [Docs]   [Start free]   │
│                                                             │
│   Every agent. Your voice.                                  │
│   ─────────────────────────────                             │
│   Vachan learns how you actually talk — your warmth,        │
│   your pacing, your Hinglish — so every reply still         │
│   sounds like you wrote it.                                 │
│                                                             │
│   [ Paste your writing ]   [See how it works]               │
│   Private details are redacted before storage.              │
│                                                             │
│   [product UI demo / Mirror preview]                        │
│                                                             │
│   Trusted by [logo] [logo] [logo] [logo]                    │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Hero visual recommendation

**Use a live, lightweight product demo in the hero.** For Vachan, the "magic" is the Mirror chat. A looping video or interactive sandbox showing a Hinglish message being sent and a coral clone reply appearing is far more convincing than a stock photo. If live interaction is too heavy for LCP, use a short, optimized video (<200KB) with a static fallback — and consider using the View Transitions API (§4.5) so clicking "See how it works" *morphs* the hero preview into the full Mirror page rather than a hard navigation cut.

### 5.4 Performance targets (source: `web.dev`, Google's own Core Web Vitals docs)

| Metric | Target | Note |
|---|---|---|
| **LCP** (Largest Contentful Paint) | < 2.5s | "Good" threshold per web.dev |
| **INP** (Interaction to Next Paint) | ≤ 200ms at the 75th percentile | Replaced FID as a Core Web Vital on **March 12, 2024**; as of 2026, ~43% of live sites still fail this threshold — it is the most commonly-failed Core Web Vital, so budget real engineering time for it, not just a Lighthouse pass |
| **CLS** (Cumulative Layout Shift) | < 0.1 | "Good" threshold per web.dev |
| Hero image/video | < 200KB | Keep the hero demo genuinely lightweight |
| Mobile tap target | ≥ 44×44px (WCAG 2.2 AA), 48×48px preferred | See §12 |

### 5.5 Code skeleton: Next.js landing page

```tsx
// frontend/app/(marketing)/page.tsx
import { Hero } from "@/components/marketing/Hero";
import { LogoBar } from "@/components/marketing/LogoBar";
import { ProblemSolution } from "@/components/marketing/ProblemSolution";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { MirrorPreview } from "@/components/marketing/MirrorPreview";
import { Testimonials } from "@/components/marketing/Testimonials";
import { Pricing } from "@/components/marketing/Pricing";
import { FAQ } from "@/components/marketing/FAQ";
import { FinalCTA } from "@/components/marketing/FinalCTA";

export default function Home() {
  return (
    <main>
      <Hero />
      <LogoBar />
      <ProblemSolution />
      <HowItWorks />
      <MirrorPreview />
      <Testimonials />
      <Pricing />
      <FAQ />
      <FinalCTA />
    </main>
  );
}
```

```tsx
// frontend/components/marketing/Hero.tsx
import Link from "next/link";
import styles from "./Hero.module.css";

export function Hero() {
  return (
    <section className={styles.hero}>
      <div className={styles.inner}>
        <p className={styles.eyebrow}>Sound like you — everywhere</p>
        <h1 className={styles.title}>Every agent. Your voice.</h1>
        <p className={styles.sub}>
          Vachan learns how you actually talk — your warmth, your pacing, your
          Hinglish — so every reply your agents send still sounds like you wrote it.
        </p>
        <div className={styles.actions}>
          <Link href="/capture" className={styles.primaryCta}>
            Paste your writing
          </Link>
          <Link href="#mirror-preview" className={styles.secondaryCta}>
            See how it works
          </Link>
        </div>
        <p className={styles.trust}>
          Private details are redacted before storage.
        </p>
      </div>
      <div className={styles.visual} aria-label="Mirror chat preview">
        {/* <MirrorPreviewVideo /> or <StaticHeroImage /> */}
      </div>
    </section>
  );
}
```

### 5.6 Anti-patterns

- Headline that says "Welcome" or uses buzzwords like "next-gen" without a concrete outcome.
- Hero that is only a screenshot of the dashboard with no transformation story.
- Multiple competing CTAs above the fold.
- Testimonials without names, roles, or photos.
- Pricing buried at the bottom without a sticky CTA on mobile.

---

## 6. Onboarding & capture flow

> **Scope:** Phase 1 web onboarding from first landing through the first Mirror chat.
> **Binding constraints:** `docs/12_FINAL_DECISIONS.md` FD-4 (cold-start bands) and FD-12 (Presidio + Indian pattern PII sanitization before storage).

### 6.1 Design basis

Vachan is a sample-driven AI product: the user must hand over personal text before anything works. That makes onboarding a **trust + time-to-value** problem, not just a signup problem.

- **Progressive disclosure beats front-loaded setup.** One primary action at a time, complexity revealed only when the user is ready.
- **Time-to-value is the top retention lever.** Every extra step before the first "win" increases drop-off.
- **Trust signals belong where hesitation peaks** — next to the action that triggers anxiety, not buried in a footer.
- **Sample-driven onboarding = show, don't tell.** Reflect back what the system understood from the user's own data immediately.

### 6.2 Flow design

The onboarding journey has **one job**: get the user to a working clone in the Mirror with the smallest possible effort and the highest possible trust.

#### Screen 0 — Landing / entry
- **Hero copy:** *"Every agent. Your voice."*
- **Primary CTA:** `Start with your voice` (coral, pill).
- **Secondary link:** `See how it works` (sand secondary).
- **Trust anchor below CTA:** *"Your writing stays on your device until private details are redacted. Read how →"*
- **Auth:** managed provider (Supabase/Clerk/Auth.js) — no custom password form. Ask only name + email; phone optional for WhatsApp export later.

#### Screen 1 — Capture method selection

A single card with three clear choices. Paste is visually dominant.

| Method | Visual weight | Why |
|---|---|---|
| **Paste your writing** | Primary (coral icon, bigger card) | Zero friction, works on all devices, fastest to value. |
| **Upload WhatsApp export** | Secondary | Higher signal, but requires a multi-tap mobile export. |
| **Build it manually** | Tertiary (ghost) | Fallback for users who don't want to share text yet. |

**Copy:**
- Headline: *"How should Vachan learn your voice?"*
- Sub: *"A few real messages are enough. We scrub the private stuff before it ever reaches us."*

#### Screen 2 — Paste input
- Large textarea (min 20 chars, suggested 200+ words for Calibrating band).
- **Placeholder:** `haan bhai, isko aise karte hain… (paste a few of your real messages)`
- Live word/token count below the field.
- Live band predictor based on word count:
  - `< 700 words` → *"Warming up — your clone will start cautious."*
  - `700–10,000 words` → *"Calibrating — solid start, more samples make it sharper."*
  - `> 10,000 words` → *"Stable — enough signal for high-confidence replies."*
- **CTA:** `Build my clone` (disabled until 20 chars).
- **Secondary:** `Try a sample` — pre-fills with safe Hinglish sample.
- **Privacy badge** pinned under the CTA.

#### Screen 3 — WhatsApp upload
- Drop zone for `.zip` / `.txt` exports. Max 50 MB.
- Helper text: *"In WhatsApp: Settings → Chats → Chat history → Export chat → Without media."*
- File picked → show **extracted message count**, **contact count redacted**, and a **preview of one sanitized snippet**.
- **CTA:** `Use these messages`.
- **Error states:** unsupported file, no readable messages, export contains media, file too large.

#### Screen 4 — Privacy reassurance / PII preview

Not a separate page; it slides in inline after paste/upload and before build.

- **Header:** *"We found some private details. Here's what we remove before saving."*
- A **diff-style preview** of one representative snippet:
  - Before: `call me on +91 98765 43210, paytm me at aakash@okicici`
  - After: `call me on [IN_PHONE], paytm me at [UPI_ID]`
- **Entity chips:** `Phone numbers`, `UPI IDs`, `Emails`, `Aadhaar/PAN`, `Indian names (flagged for review)`.
- **Badge line:** *"Sanitized locally with Presidio + Indian patterns. Only the redacted text is stored."*

#### Screen 5 — Building state
- Full-screen card with the **Building Skeleton** animation.
- Progress messages cycle every 4–6 seconds:
  1. *"Scanning for private details…"*
  2. *"Extracting your style — words, pacing, Hinglish mix…"*
  3. *"Building your Persona Capsule…"*
  4. *"Opening the Mirror…"*
- Estimated time: *"This takes 10–60 seconds depending on how much you shared."*
- Expected band surfaced up front: *"Based on ~1,400 words, your clone starts in Calibrating mode."*
- **Never** show "Indistinguishable" during this phase.

#### Screen 6 — First Mirror chat
- Clone opens with a greeting in the user's inferred register.
- **Greeting copy (Hinglish example):** *"ho gaya! ab main tere style mein baat karunga — kuch bhi pooch le 👇"*
- Fidelity Ring in the side panel shows the current band.
- Empty-state hint in the composer placeholder: `bhai project kaisa chal raha hai?`

### 6.3 Design decisions

#### One-page capture vs. wizard
**Decision: one-page capture with segmented sections, not a multi-step wizard.** A wizard adds clicks and breaks momentum for a product whose entire value depends on one paste/upload. Progress is communicated with a **3-step indicator** (Capture → Build → Mirror) that updates state, not a blocking wizard.

#### PII redaction preview
**Decision: show an inline diff preview before storage, not after-the-fact.** Seeing `[IN_PHONE]` and `[UPI_ID]` in their own text turns an abstract privacy promise into proof.

### 6.4 Error & empty states

| State | Trigger | UI treatment | Copy |
|---|---|---|---|
| **Empty paste** | `< 20 chars` | Inline warning, CTA disabled | *"Paste a little more — a few of your real messages work best."* |
| **Low signal** | `< 700 words` accepted | Inline chip + Mirror banner | *"Warming up: your clone is learning. Add more samples when you're ready."* |
| **Unsupported file** | Non-zip/txt | Inline error card | *"Please upload a WhatsApp `.txt` or `.zip` export."* |
| **No messages found** | Export empty/broken | Inline error + retry | *"We couldn't find any readable messages. Try exporting again without media."* |
| **File too large** | `> 50 MB` | Inline error | *"That file is too big. Export the chat without media, or paste a smaller section."* |
| **Network / server error** | 5xx or timeout | ErrorState component | *"We couldn't build your clone right now. Retry, or build it manually."* |
| **PII heavy** | >50% tokens redacted | Inline warning | *"Most of this text was private details. Add a few plain sentences so we can learn your style."* |

### 6.5 Anti-patterns

- Multi-step blocking wizard for a single-input product.
- Showing the PII preview only after storage instead of before.
- Overclaiming fidelity before the Stable band.
- Treating WhatsApp export as the default path (it's the higher-friction secondary).

---

## 7. The Mirror — conversational UI

### 7.1 Research basis (Nielsen Norman Group + current LLM-UI consensus)

**NN/g's own published chatbot guidelines** (from usability studies across multiple real AI-chatbot deployments) give the clearest, most checkable guidance here:

- **Capability transparency first.** State plainly what the assistant can do; don't let users guess. NN/g found that small decisions — how the bot introduces itself, whether context follows across turns, how it presents recommendations — measurably change whether people trust and keep using it.
- **Suggested prompts compensate for a generic-feeling greeting.** Showing 2–4 example questions as clickable chips at the very start lowers the "blank page" problem more effectively than trying to write a cleverer greeting line.
- **Follow-up questions must track conversation state.** Re-suggesting something the user already declined reads as "not listening" and erodes trust fast — NN/g's research specifically calls out that **visible uncertainty erodes trust slower than ambiguity does**: it's better for the assistant to say "I'm not fully confident about this" than to answer vaguely and let the user discover the gap themselves.

**Streaming UX is now the baseline, not a nice-to-have.** Across current LLM-interface guidance (UXPin, dev.to/patterns.dev-style implementation guides, and the practical behavior of every major shipped LLM product), the converged pattern is:

- Token-by-token streaming is the *expected* baseline; a reply that waits and then dumps the full text feels broken even if total latency is identical.
- The renderer must tolerate **incomplete markdown mid-stream** — a half-open `**bold` or an unclosed code fence must not corrupt layout. Buffer/defer code-block rendering until the closing fence arrives, or render it progressively with a visible "still streaming" indicator inside the block.
- **A visible stop button during generation is a real user-control expectation now**, not a power-user extra — it also directly saves inference cost.
- Each new token must not force a layout re-flow of the whole message — the container should grow without shifting surrounding elements (this is a CLS concern, see §5.4).
- Accessibility: `aria-live="polite"` + `aria-atomic="false"` on the message container, with **batched/debounced announcements** — announcing every token is unusable for screen-reader users; batch every couple of seconds instead.

### 7.2 Mirror anatomy

```
┌─────────────────────────────────────────────┬─────────────────────────────┐
│  [← Vachan.ai]  Your clone   [● warming up] │  Clone calibration          │
│  ─────────────────────────────────────────  │  [Fidelity Ring]            │
│  [Channel tabs: Chat | English | Email |    │  ─────────────────────────  │
│   Voice]                                    │  [Tonality Sliders]         │
│  ─────────────────────────────────────────  │  ─────────────────────────  │
│                                             │  [Voice KB export]          │
│  [clone bubble] haan bilkul...              │                             │
│  [user bubble]  hey can you...              │                             │
│  [clone bubble] got it — I'll share...      │                             │
│  [typing bubble] ...                        │                             │
│                                             │                             │
│  ─────────────────────────────────────────  │                             │
│  [ composer input     ] [■ Stop] [Send]     │                             │
└─────────────────────────────────────────────┴─────────────────────────────┘
```

#### Header
- Wordmark link back home.
- Clone name + status chip (`warming up`, `calibrating`, `stable`).
- Optional feedback / help menu.

#### Channel tabs
- `Chat` — casual texting, Hinglish welcome.
- `English` — same voice, English only.
- `Email` — greeting + body + sign-off.
- `Voice` — TTS-safe, short turns.

#### Message area
- Clone bubbles: left-aligned, `--coral-500` bg, `--sand-50` text, bottom-left squared.
- User bubbles: right-aligned, `--sand-200` bg, `--ink-900` text, bottom-right squared.
- Max-width: 78% desktop, 85% mobile.
- Timestamps on hover/focus only (to reduce clutter).
- **Streaming reply:** render text as it arrives; defer any fenced code block until its closing fence is seen (or show a "writing code…" placeholder inline); never re-layout already-rendered tokens.

#### Composer
- Sticky bottom input.
- Placeholder in inferred register.
- Enter to send, Shift+Enter for newline.
- **A visible Stop control appears the instant generation starts**, replacing Send; Send returns when generation completes or is stopped.

#### Side panel (desktop) / drawer (mobile)
- Fidelity Ring.
- Tonality Sliders.
- Voice KB export button.

### 7.3 Design decisions

#### Typing cadence
The current codebase already implements a word-based delay (`words * 45ms`, clamped 350–2200ms) for the *simulated* typing indicator before a reply starts. Once real streaming is wired to the LLM gateway, this delay should only gate the **typing-indicator-to-first-token** gap — once tokens start arriving, stream them as they come rather than continuing an artificial per-word delay on top of real generation latency.
- Skip the indicator delay entirely under `prefers-reduced-motion`.
- Voice channel: shorter delay, since spoken turns are expected to be brief.

#### Suggested prompts (NN/g-backed)
Show 2–4 chips above the composer on first open and after the clone greeting:
- *"Reply to a client like me"*
- *"Write a polite email to a vendor"*
- *"Say no without sounding rude"*
- *"Switch to pure Hindi"*

Do **not** re-show a chip the user has already dismissed/ignored twice in the same session — track it locally per NN/g's "don't repeat declined follow-ups" finding.

#### PII redaction in chat
When the user includes PII, show the redacted token inline in the clone reply and a subtle note: *"Phone number redacted before storage."*

### 7.4 Ghostwriter approval queue

For high-stakes messages (salary, legal, firing, finance, high-value commitments), the agent drafts in-voice and waits for one-tap approval.

```
┌─────────────────────────────────────┐
│  🔒 Sensitive — needs your approval  │
│  ─────────────────────────────────  │
│  Incoming: "We need to discuss..."  │
│  ─────────────────────────────────  │
│  [clone bubble] Draft reply...       │
│  Fidelity: 84% | Tone: polite Hindi │
│  ─────────────────────────────────  │
│  [Edit]              [Send]          │
└─────────────────────────────────────┘
```

- **Send:** coral primary.
- **Edit:** opens the draft in the composer for the user to tweak.
- **Reject:** regenerate or hand off to human.

### 7.5 Code skeletons

```tsx
// frontend/components/vachan/ChatBubble.tsx
import styles from "./ChatBubble.module.css";

export function ChatBubble({ author, children }: { author: "user" | "clone"; children: React.ReactNode }) {
  return (
    <div className={`${styles.wrap} ${styles[author]}`} aria-label={author === "clone" ? "Clone message" : "Your message"}>
      <div className={styles.bubble}>{children}</div>
    </div>
  );
}

export function TypingBubble() {
  return (
    <div className={`${styles.wrap} ${styles.clone}`} aria-live="polite" aria-label="Clone is typing">
      <div className={styles.typing}><span /><span /><span /></div>
    </div>
  );
}
```

```tsx
// frontend/components/vachan/MessageList.tsx — streaming-safe, debounced live region
import { useEffect, useRef, useState } from "react";
import { ChatBubble, TypingBubble } from "./ChatBubble";

export function MessageList({ messages, isTyping, isStreaming }: {
  messages: Msg[]; isTyping: boolean; isStreaming: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const [announced, setAnnounced] = useState("");

  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, isTyping]);

  // Batch live-region announcements every ~2s while streaming, instead of per-token.
  useEffect(() => {
    if (!isStreaming) return;
    const last = messages[messages.length - 1];
    const id = setInterval(() => setAnnounced(last?.content ?? ""), 2000);
    return () => clearInterval(id);
  }, [isStreaming, messages]);

  return (
    <div className={styles.list} role="log" aria-live="off">
      {messages.map((m, i) => <ChatBubble key={i} author={m.role}>{m.content}</ChatBubble>)}
      {isTyping && <TypingBubble />}
      <div aria-live="polite" aria-atomic="false" className="sr-only">{announced}</div>
      <div ref={endRef} />
    </div>
  );
}
```

### 7.6 Accessibility checklist for chat

- Message container: `role="log"`; live-region announcements batched (see above), not `aria-live="polite"` directly on every incoming token.
- Typing indicator has an accessible label.
- Send/Stop button has a visible label or descriptive `aria-label`, and Stop is reachable by keyboard the instant it appears.
- Focus stays in composer after sending; focus is not stolen when a reply completes.
- Color is not the only differentiator — position and rounded corners also distinguish user/clone.
- All text/background pairs pass WCAG 2.2 AA (§12).

---

## 8. Dashboard & bento layout

### 8.1 Design basis

Dashboards in the current SaaS/AI-product market are moving from "build your own charts" to **AI-native summaries that prioritize for you**:

- A single **north-star metric** dominates the top-left quadrant.
- **Progressive disclosure** everywhere: show 5–9 elements by default, hide the rest behind tabs/filters/drill-downs.
- **Color is functional**, not decorative: red = broken, green/teal = healthy, neutrals everywhere else.
- **Bento grids** encode hierarchy through tile *size*, not just labels — this is the same principle as the "hero tier vs. accent tier" distinction below.
- **Dashboard load time matters more than density.** Primary view should render in well under 2 seconds; see §5.4 for the actual Core Web Vitals thresholds this maps to.

### 8.2 Dashboard anatomy for Vachan

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Vachan.ai]        Good morning, Aakash        [🔔] [👤]           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌────────────┐  ┌────────────┐   │
│  │  Persona fidelity           │  │ Recent     │  │ Drift      │   │
│  │  [Fidelity Ring 72%]        │  │ chats      │  │ alerts     │   │
│  │  Stable — high confidence   │  │            │  │            │   │
│  └─────────────────────────────┘  └────────────┘  └────────────┘   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Your personas   │  │ Channels        │  │ Quick actions   │     │
│  │ [list]          │  │ [status grid]   │  │ [buttons]       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Tile tiers

| Tier | Content | Typical span | Example |
|---|---|---|---|
| **Hero** | Primary KPI / Fidelity Ring | 6–8 cols × 2 rows | Persona fidelity |
| **Feature** | Supporting context | 3–4 cols × 1–2 rows | Recent chats |
| **Metric** | Secondary KPI / status | 2–3 cols × 1 row | Drift alerts count |
| **Accent** | Quick action / alert | 2 cols × 1 row | Add sample, approve draft |

### 8.3 Design decisions

#### North star metric
The headline metric is the **highest-confidence persona fidelity score** across the user's personas. It answers: *"Is my voice still sounding like me?"*

#### Color coding
- **Teal:** on-voice, connected, healthy.
- **Amber:** drifting, setup needed, provisional.
- **Rose:** off-voice, blocked, error.
- Never rely on color alone — pair with icon + label (WCAG 2.2 — see §12).

#### Empty states
- **No personas:** Warm illustration + *"You don't have a voice capsule yet. Paste a few messages to build one."*
- **No chats:** *"No conversations yet. Open the Mirror to test your clone."*
- **All healthy:** *"All quiet. Your clones are sounding like you."*

#### Responsive behavior — now a subgrid + container-query job, not breakpoint duplication
With the tools in §4, each bento tile can declare its own internal layout via `container-type` rather than the page owning every tile's internal responsiveness through global breakpoints, and the row-level alignment (title/body/footer across tiles of different content length) is a `subgrid` job, not manual padding tweaks:

```css
.grid {
  display: grid;
  gap: 20px;
  padding: 24px;
  max-width: 1280px;
  margin: 0 auto;
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(12, 1fr);
    grid-template-areas:
      "hero hero hero hero hero hero recent recent recent alert alert alert"
      "hero hero hero hero hero hero recent recent recent alert alert alert"
      "personas personas personas personas channels channels channels quick quick quick quick quick";
  }
  .hero { grid-area: hero; }
  .recent { grid-area: recent; }
  .alert { grid-area: alert; }
  .personas { grid-area: personas; }
  .channels { grid-area: channels; }
  .quick { grid-area: quick; }
}

@media (min-width: 640px) and (max-width: 1023px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .hero { grid-column: span 2; }
}

@media (max-width: 639px) {
  .grid { grid-template-columns: 1fr; }
}
```

### 8.4 Anti-patterns

- Showing every metric the backend can compute.
- Equal-sized cards competing for attention.
- Using coral for success.
- Dashboards that require users to build their own view before seeing value.

---

## 9. Persona detail — capsule editor & version timeline

### 9.1 Design basis

Settings/detail pages for AI/ML products consistently converge on:

- **Split-pane editors**: a friendly form on one side, the structured underlying record on the other — this builds trust by showing users exactly what the system stored (directly serves FD-7).
- **Read-only vs. editable modes**, preventing accidental edits to derived AI outputs.
- **Version control as semantic diffs**, not raw timestamps — users should understand *what changed*, not just *when*.
- **Progressive disclosure for complexity** — hide raw embeddings, token counts, and provenance hashes behind an "Advanced" fold.

### 9.2 Page anatomy

```
┌─────────────────────────────────────────────────────────────────────┐
│  [← Back]  Aakash (work)              [Edit] [Export] [Rollback]    │
├──────────────────────────────┬──────────────────────────────────────┤
│  Identity                    │  Capsule preview (YAML)              │
│  • Name, description         │  ─────────────────────────────────   │
│  • Tags, channel defaults    │  version: 12                         │
│                              │  confidence: 0.84                    │
│  Tone                        │  steering:                           │
│  • Warmth, directness        │    warmth: 0.62                      │
│  • Formality, Hinglish mix   │    directness: 0.51                  │
│                              │    formality: 0.40                   │
│  Language                    │    hinglish: 0.33                    │
│  • CMI target                │  language:                           │
│  • Script preferences        │    cmi_target: 0.33                  │
│                              │    script: "roman"                   │
│  Do / Don't                  │  do:                                 │
│  • Chips + add new           │    - "use yaar with peers"           │
│                              │  dont:                               │
│  Provenance                  │    - "use formal Hindi with elders"  │
│  • Evidence tokens           │                                      │
│  • Last calibrated           │                                      │
├──────────────────────────────┴──────────────────────────────────────┤
│  Version history                                                    │
│  ● v12 now     Stable, Hinglish 29%→35%, formality 0.62→0.49        │
│  ○ v11 2d ago  Added WhatsApp samples                               │
│  ○ v10 5d ago  Manual baseline                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 Design decisions

- **Split view: friendly form + YAML preview.** Left: form fields (name, description, tone sliders, language mix, do/don't chips). Right: read-only YAML rendered from the structured record (per FD-7). YAML editing is Phase 2+ and must go through validation + a preview diff.
- **Version timeline:** vertical, newest first. Each node: version number, date, band, and a **semantic diff** in plain English (e.g. *"Hinglish 29% → 35%, formality 0.62 → 0.49, added 'scene kya hai'."*). **Rollback** creates a new version rather than deleting history (append-only log, per the DB's own append-only trigger design).
- **Confidence and provenance chips:** `confidence: 0.84` with a small progress bar; `evidence_tokens: 14,200`; `last_calibrated: 2 hours ago`; provenance link to the audit log.

### 9.4 Code skeleton

```tsx
// frontend/app/personas/[id]/page.tsx
import { PersonaHeader } from "@/components/vachan/PersonaHeader";
import { CapsuleForm } from "@/components/vachan/CapsuleForm";
import { CapsuleYamlPreview } from "@/components/vachan/CapsuleYamlPreview";
import { VersionTimeline } from "@/components/vachan/VersionTimeline";
import styles from "./page.module.css";

export default function PersonaDetailPage({ params }: { params: { id: string } }) {
  return (
    <main className={styles.page}>
      <PersonaHeader personaId={params.id} />
      <div className={styles.split}>
        <CapsuleForm personaId={params.id} />
        <CapsuleYamlPreview personaId={params.id} />
      </div>
      <VersionTimeline personaId={params.id} />
    </main>
  );
}
```

### 9.5 Anti-patterns

- Letting users edit raw YAML without validation.
- Showing raw embedding vectors by default.
- Deleting old versions instead of appending.
- Using technical jargon like "centroid distance" in the default view.

---

## 10. Channels connector

### 10.1 Design basis

Integration UX for multi-channel SaaS converges on a few durable rules:

- **One-click connect where possible.** OAuth flows should require the fewest steps; explain what permissions are needed and why.
- **Status must be glanceable** — connected/setup-needed/error readable at a glance without opening a detail view.
- **Progressive setup** for multi-step channels (e.g. WhatsApp Business verification): show a clear checklist, not a black box.
- **Channel-specific fidelity:** users should see whether a channel is "on-voice" or needs calibration per channel.

### 10.2 Connector grid spec

| Channel | Default state | Notes |
|---|---|---|
| **Web / Mirror** | Connected | The primary surface. |
| **WhatsApp** | Setup needed | Requires Meta Cloud API + business verification concierge. |
| **Telegram** | Setup needed | Bot API supports streaming AI replies. |
| **Slack** | Deferred (V2+) | OAuth workspace install. |
| **Voice (Vapi/Retell)** | Setup needed | Exports signed Capsule Bundle + voice KB. |
| **MCP live-mount** | Setup needed | For agents that can call Vachan tools live. |

### 10.3 Card anatomy

```
┌─────────────────────────────┐
│  [icon]  WhatsApp           │
│  Setup needed               │
│  ─────────────────────────  │
│  Business verification      │
│  pending.                   │
│  [Continue setup]           │
└─────────────────────────────┘
```

**States:** Connected → teal dot + *"Live"*. Setup needed → amber dot + *"Continue setup"*. Error → rose dot + error message + *"Reconnect"*. Unavailable → muted dot + *"Coming soon"*.

### 10.4 Code skeleton

```tsx
// frontend/components/vachan/ChannelCard.tsx
import styles from "./ChannelCard.module.css";

const STATUS_STYLES = {
  connected: { dot: styles.teal, label: "Live" },
  setup_needed: { dot: styles.amber, label: "Setup needed" },
  error: { dot: styles.rose, label: "Error" },
  unavailable: { dot: styles.muted, label: "Coming soon" },
};

export function ChannelCard({ label, status }: { label: string; status: keyof typeof STATUS_STYLES }) {
  const s = STATUS_STYLES[status];
  return (
    <div className={styles.card}>
      <div className={styles.head}>
        <span className={styles.title}>{label}</span>
        <span className={styles.status}><span className={s.dot} /> {s.label}</span>
      </div>
      {status === "setup_needed" && <button className={styles.action}>Continue setup</button>}
    </div>
  );
}
```

### 10.5 Anti-patterns

- Hiding channel errors behind a tooltip.
- Asking for permissions without explaining why.
- Showing channels the user cannot actually enable in their region/plan.

---

## 11. Motion, animation & micro-interactions

### 11.1 Research basis: Emil Kowalski's rules + Rauno Freiberg's "invisible details"

The most checkable, currently-referenced authority on exactly this craft level is **Emil Kowalski** and **Rauno Freiberg** — two design engineers who both worked at Vercel and now work together at Linear, and who each publish their reasoning in public (Kowalski at `emilkowal.ski`, Freiberg's writing collected in pieces like *"Invisible Details of Interaction Design"*). Their work is the de facto reference for "why does Linear/Vercel/Arc *feel* more expensive than a template," which is precisely the question this section answers.

**Kowalski's animation framework** (43 rules across 7 categories — Easing Selection, Timing & Duration, Property Selection, Transform Techniques, Interaction Patterns, Strategic Animation, Accessibility & Polish) reduces to a few load-bearing principles:

1. **Every animation must answer "why does this animate?"** — the legitimate reasons are: spatial consistency (where did this element come from/go to), state indication, explanation of a relationship, direct feedback, or preventing a jarring change. "Because it looks nice" is not on the list.
2. **Never animate keyboard-initiated, high-frequency actions.** Typing, arrow-key navigation, and similar repeated-hundreds-of-times-daily actions must feel instant — animation on these reads as *latency*, not polish.
3. **Default to ease-out for entrances; use custom cubic-bezier, not the CSS keyword `ease`.** Spring/iOS-drawer-style easings are reserved for specific interaction patterns (drag, sheet dismissal), not applied blanket.
4. **Timing guardrails: keep UI feedback under ~300ms.** This matches what was already in this doc's motion-token table (§11.2 below) — it was directionally correct, it now has a named, checkable source instead of an aggregated blog citation.

**Freiberg's "invisible details" principle:** the details that separate a $100k build from a template are usually **one deliberate micro-interaction per frequently-used component**, executed with real care (his own example: a tooltip whose position subtly adapts to available space, so it never seems to fight the cursor) — not more animation everywhere. This directly informs §15's "where to actually spend craft hours" list.

### 11.2 Motion tokens (unchanged — already correctly scoped)

```css
:root {
  --duration-instant: 80ms;
  --duration-fast:    150ms;
  --duration-normal:  250ms;
  --duration-slow:    400ms;
  --duration-enter:   500ms;

  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-snap: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### 11.3 Component-level motion specs

| Element | Trigger | Duration | Easing | Transform | Kowalski rule applied |
|---|---|---|---|---|---|
| Button hover | hover | 200ms | --ease-spring | translateY(-1px) + shadow lift | feedback |
| Button press | active | 80ms | --ease-snap | scale(0.97) | feedback, instant-feeling |
| Card hover | hover | 250ms | --ease-out | translateY(-4px) + shadow-md | state indication |
| Chat bubble | mount | 300ms | --ease-out | translateY(8px)→0, opacity 0→1 | spatial consistency (arrives from below, like a message "landing") |
| Fidelity ring | value change | 600ms | --ease-out | stroke-dashoffset animate | explanation (shows the delta, not just the new number) |
| Slider thumb | drag | 150ms | --ease-snap | scale(1.1) on active | feedback |
| Composer text input | every keystroke | **none** | — | — | Kowalski rule 2 — never animate typing |
| Modal/drawer | open | 300ms | --ease-out | translateY(20px)→0, opacity 0→1 | spatial consistency |
| Route change (simple) | navigation | native | View Transitions (§4.5) | cross-fade / shared-element morph | replaces hand-rolled page-transition wrapper |

### 11.4 Library recommendations

| Use case | Tool | Why |
|---|---|---|
| Component micro-interactions (chat bubbles, cards, sliders) | **Framer Motion** | Declarative, React-native, built-in reduced-motion handling, real spring physics for the cases that need it. |
| Simple route/page transitions | **View Transitions API** (native, §4.5) | Zero extra dependency for the cases that are just cross-fade/morph; Next.js has first-class support as of 2026. |
| Scroll-driven landing-page effects (progress bar, entrance reveals) | **Native CSS `animation-timeline`** (§4.4) | Runs on the compositor thread — smoother than a JS scroll listener, and removes a GSAP/ScrollTrigger dependency for the simple cases. |
| Genuinely complex scroll choreography (if ever needed) | **GSAP + ScrollTrigger** | Still the right escape hatch for orchestration native CSS can't yet express — but confirm the native tools in §4 don't already cover the need first. |
| Simple CSS transitions | **CSS modules** | No JS overhead for hover/press states. |

**This is one real change from v1:** native CSS (scroll-driven animations, View Transitions) now covers cases that used to require Framer Motion or GSAP, so the dependency list should get *smaller* over time, not bigger.

### 11.5 Code skeletons

```tsx
// frontend/hooks/useReducedMotion.ts
import { useEffect, useState } from "react";

export function useReducedMotion() {
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduce(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduce(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return reduce;
}
```

```css
@media (prefers-reduced-motion: reduce) {
  .button { transition: box-shadow var(--duration-fast) ease; }
  .button:hover { transform: none; }
}
```

### 11.6 Anti-patterns

- Animating layout properties (`width`, `height`, `top`) instead of `transform`/`opacity`.
- Animating anything that fires on every keystroke.
- Bounce/elastic easing on functional, high-frequency UI.
- Long animations that block the next interaction.
- Ignoring `prefers-reduced-motion`.
- Reaching for GSAP/Framer for something native `animation-timeline` or View Transitions already solves for free.

---

## 12. Accessibility, inclusion & Hinglish UX

### 12.1 What's actually true: WCAG 2.2 is current, WCAG 3.0 is years away

**WCAG 2.2 is the binding standard right now** — it was published as a formal W3C Recommendation on 5 October 2023, and was separately approved as **ISO/IEC 40500:2025** in October 2025, which is what regulatory frameworks (ADA, Section 508, EAA) actually reference. **WCAG 3.0 is still a Working Draft** (most recently updated March 2026, covering ~174 outcomes across 12 categories); the W3C's own timeline puts a Candidate Recommendation around **Q4 2027** and a final Recommendation **no earlier than 2028**. WCAG 3.0's own Bronze conformance tier is explicitly scoped to be "roughly equivalent to WCAG 2.2 AA" — so building to 2.2 AA now is not wasted effort, it is the on-ramp to 3.0 later.

**Practical implication for Vachan:** target **WCAG 2.2 Level AA** as the binding bar. Do not delay accessibility work waiting for WCAG 3.0 — it won't be final for years, and 2.2 will not be deprecated when it ships.

**What's new specifically in 2.2** relative to 2.1 (the version most teams still default to): target size minimum (2.5.8, ≥24×24px, with Vachan already targeting the stricter 44–48px), consistent help placement (3.2.6), redundant entry (3.3.7 — don't make users re-enter info they already gave), and accessible authentication (3.3.8 — no cognitive-function-only tests like a puzzle CAPTCHA as the sole login method).

### 12.2 Accessibility strategy for Vachan

#### Contrast (WCAG 2.2 §1.4.3 / §1.4.11)

| Pair | Ratio target | Notes |
|---|---|---|
| `--ink-900` on `--sand-50` | ≥ 4.5:1 | Body text |
| `--ink-700` on `--sand-100` | ≥ 4.5:1 | Secondary text |
| `--sand-50` on `--coral-500` | ≥ 4.5:1 | Clone bubble text |
| `--coral-700` on `--sand-50` | ≥ 4.5:1 | Links |
| Focus ring | ≥ 3:1 against adjacent | `--coral-500` 2px offset |
| Non-text UI (icons, status dots) | ≥ 3:1 | WCAG 2.2 §1.4.11 |

#### Keyboard & focus
- All interactive elements reachable by `Tab`.
- Visible focus ring on everything: `outline: 2px solid var(--coral-500); outline-offset: 2px;`.
- Modal/drawer traps focus and returns it on close.
- Skip-to-main-content link on every page.
- Logical heading hierarchy (`h1` → `h2` → `h3`, no skips).
- **New in 2.2 — consistent help:** if a help/support link exists, it must appear in the same relative order across pages.
- **New in 2.2 — redundant entry:** the capture flow already gets this right by design (one paste, everything derived) — don't regress it later by asking users to re-enter anything (name, language) they already gave during signup.

#### Screen readers
- Chat message container: batched live-region announcements (§7.1/§7.5), not raw `aria-live="polite"` on every token.
- Icon-only buttons have `aria-label`.
- Form errors linked with `aria-describedby` and announced via `role="alert"`.

### 12.3 Hinglish & multilingual UX

- **Automatic language detection.** Do not force the user to select a language.
- **Romanized Hinglish is valid text.** Do not autocorrect `yaar`, `arre`, `scene`, `matlab` to English.
- **Lang attributes.** Wrap Hindi-script output in `<span lang="hi">` and English in `<span lang="en">` when the script switches within a message — this is what lets a screen reader actually switch pronunciation engines mid-sentence instead of reading Hindi script with an English voice.
- **Code-switch slider.** The Tonality Slider exposes a "Hinglish mix" control, live in Phase 1.
- **Voice-note UI.** Show waveform, allow replay, indicate that prosody is being captured.

### 12.4 Testing checklist

- [ ] Run axe DevTools / Lighthouse on every page (catches roughly a third to a half of real issues — the rest requires manual testing, not a tooling gap to skip).
- [ ] Navigate the entire main flow with keyboard only.
- [ ] Test with VoiceOver (macOS) and NVDA (Windows).
- [ ] Enable `prefers-reduced-motion` and verify no essential info is lost.
- [ ] Test at 200% browser zoom and 320px mobile width.
- [ ] Verify color is not the only means of conveying status.
- [ ] Confirm no cognitive-function-only step (e.g. a CAPTCHA) is the *sole* path to authenticate (WCAG 2.2 §3.3.8).

### 12.5 Anti-patterns

- Placeholder-only labels.
- Removing focus rings for "cleanliness."
- Relying on color alone for error/success.
- Forcing users to pick a single language before typing.
- Transliterating user text against their will.
- Treating WCAG 3.0 as a reason to delay 2.2 AA work — it is not shipping for years.

---

## 13. Frontend architecture & component strategy

### 13.1 What's actually true in 2026

- **Tailwind CSS v4.0** shipped 22 January 2025 — a ground-up rewrite on the Rust-based **Lightning CSS** engine (full builds up to 5x faster, incremental builds over 100x faster), CSS-first configuration (`@import "tailwindcss"` + `@theme`, no more `tailwind.config.js` as the primary surface), and native use of cascade layers, `@property`, and `color-mix()`. **v4.3 (July 2025)** added first-party scrollbar styling, logical-property utilities, and a `not-*` variant. This is the version to build on — the JS-config-file mental model from v3 docs is now out of date.
- **Base UI has overtaken Radix UI** as the actively-developed headless primitive layer. Radix was acquired by WorkOS and its update pace slowed; Base UI (built by the MUI/Material-UI team) now has dedicated full-time engineering behind it. **shadcn/ui itself now supports both as swappable backends** — when scaffolding a new shadcn project you pick Radix or Base UI as the engine, same component API either way. For a new build in 2026, **default to the Base UI backend.**
- **shadcn/ui remains the right consumption model**: it copies typed component source directly into the repo rather than shipping a black-box npm dependency, so the team owns and can modify every primitive.

### 13.2 Recommended architecture for Vachan

```
frontend/
├── app/
│   ├── globals.css           # tokens + base reset
│   ├── theme.css             # Tailwind v4 @theme mapping
│   ├── layout.tsx            # fonts + providers
│   ├── (marketing)/          # landing, pricing, about
│   ├── capture/               # onboarding capture
│   ├── mirror/                # chat sandbox
│   ├── dashboard/             # bento dashboard
│   ├── personas/[id]/         # detail + version timeline
│   └── channels/              # connector grid
├── components/
│   ├── ui/                    # shadcn-style primitives (Base UI backend)
│   ├── vachan/                # product-specific components
│   └── marketing/             # landing page sections
├── lib/
│   ├── utils.ts                # cn() + helpers
│   ├── backend.ts              # API client
│   └── tokens.ts                # typed token access (generated from tokens.json, §3.5)
└── hooks/
    ├── useReducedMotion.ts
    └── usePersona.ts
```

### 13.3 Tailwind v4 + shadcn/ui (Base UI backend) skeleton

```bash
npm install tailwindcss@latest @tailwindcss/postcss
npx shadcn@latest init   # choose Base UI when prompted for the primitive engine
npx shadcn add button card dialog slider tabs
```

```css
/* frontend/app/theme.css — Tailwind v4 CSS-first config */
@import "tailwindcss";

@theme {
  --color-sand-50: var(--sand-50);
  --color-coral-500: var(--coral-500);
  --color-ink-900: var(--ink-900);
  --font-display: var(--font-fraunces), Georgia, serif;
  --radius-lg: var(--radius-lg);
  --shadow-md: var(--shadow-md);
}
```

```ts
// frontend/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 13.4 Data flow diagram

```
User paste/upload
    │
    ▼
/api/capture/preview  ──► Presidio + Indian patterns PII redaction
    │
    ▼
/api/capture/build    ──► FastAPI tone engine ──► Persona Capsule
    │
    ▼
Mirror chat (/mirror) ──► /api/mirror/chat ──► generate + score fidelity (streamed, §7)
    │
    ▼
Ghostwriter queue ──► /api/ghostwriter/rewrite ──► approval ──► send
    │
    ▼
Channels ──► MCP live-mount or Capsule Export Bundle
```

### 13.5 GraphQL vs REST vs MCP

- **GraphQL is not required.** Vachan's backend is FastAPI with clear request/response contracts (`/capture`, `/mirror/chat`, `/ghostwriter/rewrite`, `/channels`). Adding GraphQL introduces schema maintenance, caching complexity, and tooling overhead without solving a real problem here.
- **REST remains the default** for web frontend ↔ backend.
- **MCP is the cross-agent contract** (FD-8) — Vachan exposes MCP tools (`render_in_persona`, `retrieve_knowledge`, `score_fidelity`) so external agents can live-mount a voice.
- **Capsule Export Bundle** is the offline/portable contract for voice platforms that cannot keep a live connection.

### 13.6 Anti-patterns

- CSS-in-JS (Styled Components/Emotion) in a Next.js App Router project — breaks RSC boundaries and adds runtime cost that Tailwind v4's compiled CSS doesn't have.
- Hardcoding hex values in components — always reference tokens.
- Building every component from scratch instead of using Base UI primitives for dialogs/selects/comboboxes.
- Putting all state in global stores; prefer URL state + server state (React Query/SWR) + local UI state.
- Assuming Radix UI is still the default choice without checking — it isn't anymore (§13.1).

---

## 14. Content & copy strategy

### 14.1 Principles

- **Clarity over cleverness.** Users skim; front-load meaning in headings and CTAs.
- **AI transparency is required, not optional.** Users must know when AI is generating content, how confident it is, and what its limits are — this is now standard practice across IBM's Carbon for AI guidelines and Apple's HIG for machine learning, and it's directly required by Vachan's own FD-1 (never overclaim fidelity below Stable).
- **Error recovery copy blames the system, not the user.** *"We couldn't…"* not *"You failed to…"*
- **Tone shifts by context; voice stays constant.** Calm in errors, warm in onboarding, neutral in governance.

### 14.2 Voice & tone principles

| Principle | Do | Don't |
|---|---|---|
| **Warm but precise** | *"Your clone is warming up."* | *"AI model initialising…"* |
| **Honest about limits** | *"This score is provisional until we calibrate it with more samples."* | *"100% accurate."* |
| **India-proud, world-class** | *"Made in India, for how India actually talks."* | *"Desi alternative to ChatGPT."* |
| **Action-oriented** | *"Paste your writing"* | *"Submit input data"* |
| **Human recovery** | *"We couldn't build your clone right now. Retry, or build it manually."* | *"Error 500."* |

### 14.3 Microcopy table

| Location | Copy |
|---|---|
| Primary CTA (landing) | `Paste your writing` |
| Secondary CTA | `See how it works` |
| Privacy badge | *"Private details are redacted before storage."* |
| Mirror composer placeholder | `bhai project kaisa chal raha hai?` |
| Fidelity provisional chip | *"Provisional — calibrating with more samples."* |
| Drift alert | *"Your clone is drifting toward generic replies. Add a recent sample."* |
| Ghostwriter card | *"This message looks sensitive. Here's a draft in your voice."* |
| Empty dashboard | *"No personas yet. Paste a few messages to build your first voice."* |
| Error retry | `Try again` |

### 14.4 Terminology glossary

| Term | Use it for | Avoid |
|---|---|---|
| **Persona Capsule** | The stored voice identity. | "Profile," "template." |
| **The Mirror** | Sandbox chat with your clone. | "Demo," "playground." |
| **Fidelity** | How close output sounds to the person. | "Accuracy," "quality score." |
| **Ghostwriter** | Draft-in-voice approval queue. | "Approval workflow." |
| **Hinglish mix** | Code-switching intensity. | "Hindi ratio." |

### 14.5 Anti-patterns

- AI hype words: "magic," "revolutionary," "next-gen."
- Vague error messages: "Something went wrong."
- Blaming the user in error copy.
- Overusing English in Hinglish-first contexts.
- Hiding AI involvement.

---

## 15. What "$100k of craft" actually buys — and how we get it for less

### 15.1 What the money actually pays for

Current market data on premium/custom web design pricing is directionally consistent: **premium custom builds range roughly $7,500–$25,000+** for a marketing site, climbing to **$15,000–$50,000+** for complex, multi-page products with bespoke UX and animation, at **$125–$300/hour** for senior design-engineering time. The load-bearing detail, though, is *what the extra money is actually buying* — market analysis consistently points to two things: **design originality** (roughly 20–40 hours of dedicated UX research and iteration per major surface, not template customization) and **content operations** (professional copywriting and original photography/imagery direction, often $2,000–$5,000 on its own). It is **not**, primarily, buying exotic technology — Stripe, Linear, and Vercel (the three reference points every "premium SaaS" conversation eventually points to) all run on fairly ordinary React/CSS stacks. What they share instead:

- **High contrast, monochrome-first color** — black on white, white on black, nothing muddy in the middle, with color reserved for the one thing that needs to stand out.
- **Whitespace treated as "air," not emptiness** — consistently *more* space around elements than instinct says is necessary.
- **All six interactive microstates actually designed** — default, hover, focus, active, disabled, loading — not just default+hover with the rest left to the browser.
- **Systematic, specific decisions everywhere**, not framework defaults left untouched.

### 15.2 Translating that into a Vachan-specific checklist

Given the research above, this is where a small team should spend disproportionate craft time — the "20–40 hours of dedicated iteration" the market data describes, concentrated rather than spread thin:

1. **The Mirror's chat bubble entrance and the Fidelity Ring's value-change animation** — these are the two surfaces a user watches most closely and most often; per Freiberg's "invisible details" principle (§11.1), this is where one deliberate, well-executed micro-interaction matters more than broad animation coverage elsewhere.
2. **All six microstates on `Button`, `Card`, `Slider`, and the composer input** — audit right now: does `disabled` look meaningfully different from `default`? Does `loading` exist as a real state or does the button just... sit there? This is the single highest-leverage, lowest-cost item on this list.
3. **The hero's product demo** (§5.3) — this is the one asset worth real production value (a genuinely well-shot/edited short capture of the Mirror in use), because it is the thing every visitor sees first and it directly substitutes for "immersive 3D" (§15.3) at a fraction of the engineering cost.
4. **Copy, end to end** — §14 already encodes this; professional copy tightening is one of the two things the pricing data says actually separates premium from template, and it costs editing time, not engineering time.
5. **The variable-font optical-size wiring for Fraunces (§3.2)** — a small, one-time technical task that measurably changes how "designed" the display type feels at every size, for near-zero ongoing cost.

### 15.3 What to deliberately skip

Awwwards' own current site-of-the-year archive is dominated by **WebGL/3D interactive experiences and heavy scroll-driven storytelling** (recent honorees lean hard into real-time 3D environments and browser-based interactive worlds). That is a legitimate creative direction for a portfolio or a car launch — **it is the wrong direction for Vachan.** The product's entire premise is *calm, trustworthy, gets out of the way* (§1 north star); a WebGL hero would directly fight that identity and would also blow the LCP/INP budget in §5.4. Chase the craft-density items in §15.2, not the Awwwards trend list — this is an explicit, deliberate editorial call, not an oversight.

---

## 16. Page-by-page design decisions

| Page / surface | Primary goal | Key design decision | Grounded in |
|---|---|---|---|
| **Landing** | Convert in <5s | Single primary CTA, real product demo in hero, named social proof | §5, §15.2 (hero as the one asset worth real production value) |
| **Auth / signup** | Low-friction entry | Managed provider, name+email only, phone optional | §6.2 Screen 0 |
| **Capture** | Build trust + first capsule | One-page capture, live PII preview, band predictor | §6, FD-4, FD-12 |
| **Building state** | Make wait feel intentional | Skeleton with 4 cycling steps, never overclaim band | §6.2 Screen 5, FD-1 |
| **Mirror** | Wow + tune | Coral=clone, sand=user, suggested prompts, streaming-safe renderer, Ghostwriter queue | §7, NN/g chatbot guidelines |
| **Dashboard** | Surface health at a glance | Bento grid + subgrid alignment, north-star fidelity, 5–9 default elements | §8, §4.3 |
| **Persona detail** | Govern + iterate | Split form/YAML view, semantic version diff, rollback | §9, FD-7 |
| **Channels** | Connect voice everywhere | Glanceable status cards, WhatsApp concierge, MCP export | §10, FD-8/FD-9 |
| **Settings** | Consent + data control | DPDP-aligned export/delete, clear data usage | §12 accessibility + privacy overlap |

---

## 17. Implementation roadmap

### Phase 0 — Foundations (now)
- [ ] Install Tailwind CSS v4 (already GA since Jan 2025) + shadcn/ui with the **Base UI** backend (§13.1).
- [ ] Port existing CSS tokens to `@theme` mapping; regenerate the color ramp in OKLCH (§3.1) while keeping shipped hex values stable.
- [ ] Wire Fraunces as a true variable font with `opsz` bound to font-size (§3.2) — currently likely loaded as static weights.
- [ ] Refactor `Button`, `Card`, `ChatBubble` to Base-UI-backed shadcn style + CVA, with all six microstates actually designed (§15.2).
- [ ] Add `cn()` utility, `useReducedMotion` hook, focus-visible styles.
- [ ] Set up accessibility linting (axe-core / eslint-plugin-jsx-a11y) in CI against WCAG 2.2 AA (§12).

### Phase 1 — Web Mirror MVP
- [ ] Implement capture screen with live band predictor and PII preview.
- [ ] Build `BuildingSkeleton` and transition to `/mirror?personaId=`.
- [ ] Wire the Mirror to real token streaming: buffered markdown, deferred code-fence rendering, visible Stop control, batched live-region announcements (§7.1/§7.5).
- [ ] Add suggested prompts (with "don't re-show a declined chip" logic) and Ghostwriter approval card UI.
- [ ] Apply container queries to `ChannelCard`/`GhostwriterCard` instead of viewport-only breakpoints (§4.1).
- [ ] Landing page with hero, social proof, Mirror preview, FAQ; consider a View-Transitions morph from hero preview → full Mirror (§5.3, §4.5).

### Phase 2 — Dashboard + Channels
- [ ] Build bento dashboard with subgrid-aligned tiles, empty states.
- [ ] Build persona detail page with split view and version timeline.
- [ ] Build channels connector grid with status variants.
- [ ] Add dark mode toggle; re-validate contrast and confirm elevation is luminance-based, not shadow-based (§3.3).

### V1+ — Polish & scale
- [ ] Add micro-interactions across buttons, cards, chat bubbles, rings — per Kowalski's "why does this animate" test (§11.1), not blanket coverage.
- [ ] Implement Hinglish `lang` annotations and transliteration helpers.
- [ ] Migrate the token set to W3C DTCG format (`tokens.json`) once it stabilizes, generating both CSS variables and Figma variables from one source (§3.5).
- [ ] Add MCP live-mount documentation and Capsule Export Bundle UI.
- [ ] Run a full accessibility audit with real assistive tech, plus a WCAG 2.2 §3.3.7/§3.3.8 pass (redundant entry, accessible auth).

---

## 18. Handoff checklist

### Visual system
- [ ] No hardcoded hex in components; all colors reference tokens.
- [ ] Color ramp authored in OKLCH, compiled to the shipped hex custom properties (§3.1).
- [ ] Fonts loaded via `next/font`; Fraunces loaded as a variable font with `opsz` wired to size (§3.2).
- [ ] Dark mode tokens defined, contrast-checked, and elevation done via lightness steps rather than heavier shadows (§3.3).
- [ ] Spacing values come from the 4px scale, with fluid `clamp()` section rhythm (§3.4).

### Modern CSS
- [ ] Container queries used for at least the bento tiles and card components that currently rely on viewport breakpoints (§4.1).
- [ ] Subgrid used to align multi-column card rows instead of manual padding math (§4.3).
- [ ] Scroll-driven `animation-timeline` used only where it replaces a JS scroll listener with a clear compositor-thread win (§4.4).

### Components
- [ ] All primitives (Button, Card, Input, Slider, Dialog) have default/hover/focus/active/disabled/loading states — genuinely designed, not left to browser defaults (§15.2).
- [ ] Vachan-specific components (ChatBubble, FidelityRing, TonalitySliders, GhostwriterCard, VersionTimeline, ChannelCard) implemented.

### Pages
- [ ] Landing, capture, Mirror, dashboard, persona detail, channels all render.
- [ ] Each page has a single primary CTA.
- [ ] Responsive behavior verified at 320px, 375px, 768px, 1024px, 1440px.

### Motion
- [ ] Motion tokens documented and used consistently; every animation traceable to one of Kowalski's stated reasons (§11.1).
- [ ] Nothing animates on keystroke or other high-frequency keyboard input.
- [ ] `prefers-reduced-motion` respected everywhere.
- [ ] No layout-property animations; only `transform`/`opacity`, or native `animation-timeline`.
- [ ] Simple route transitions use the View Transitions API rather than a hand-rolled wrapper (§4.5).

### Accessibility
- [ ] WCAG 2.2 AA contrast met for all text/background and non-text UI pairs.
- [ ] Full keyboard navigation works for main flows.
- [ ] Focus management implemented for modals/drawers.
- [ ] Streaming chat announcements are batched, not per-token (§7.1/§7.5).
- [ ] Touch targets ≥ 44×44px minimum, 48×48px preferred.
- [ ] No cognitive-function-only step is the sole authentication path (§12.1).

### Performance
- [ ] LCP < 2.5s, INP ≤ 200ms at p75, CLS < 0.1 on mobile — measured against real `web.dev` definitions, not just a single Lighthouse run (§5.4).
- [ ] Hero image/video < 200KB.
- [ ] Animation runs at 60fps on mid-range Android; scroll-driven effects confirmed to run off the main thread.

### Copy
- [ ] UI copy reviewed against voice & tone principles (§14).
- [ ] All AI-generated content labeled; fidelity never overclaimed below Stable band (FD-1).
- [ ] Error messages explain the problem and next step, blaming the system not the user.

---

## 19. Source list (verified)

Every URL below was returned by a live web search on 2026-07-01 while writing this edition — none are synthesized. Organized by topic, highest-authority sources first within each group.

### Color
- MDN — `oklch()` CSS function: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch
- Evil Martians — *OKLCH in CSS: why we moved from RGB and HSL*: https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl

### Typography
- Utopia — *Fluid type scale calculator*: https://utopia.fyi/type/calculator/
- Utopia — *Clamp*: https://utopia.fyi/blog/clamp/
- Smashing Magazine — *Meet Utopia: Designing And Building With Fluid Type And Space Scales*: https://www.smashingmagazine.com/2021/04/designing-developing-fluid-type-space-scales/
- OddBird — *Reimagining Fluid Typography*: https://www.oddbird.net/2025/02/12/fluid-type/

### Modern CSS
- MDN — *Scroll-driven animation timelines*: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations/Timelines
- Chrome for Developers — *CSS scroll-triggered animations are coming!*: https://developer.chrome.com/blog/scroll-triggered-animations
- Josh W. Comeau — *Scroll-Driven Animations*: https://www.joshwcomeau.com/animation/scroll-driven-animations/
- MDN — *View Transition API*: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API
- Next.js docs — *Guides: View transitions*: https://nextjs.org/docs/app/guides/view-transitions

### Performance / Core Web Vitals
- web.dev — *Interaction to Next Paint (INP)*: https://web.dev/articles/inp
- web.dev — *Interaction to Next Paint becomes a Core Web Vital on March 12*: https://web.dev/blog/inp-cwv-march-12
- web.dev — *How the Core Web Vitals metrics thresholds were defined*: https://web.dev/articles/defining-core-web-vitals-thresholds

### Accessibility
- W3C — *Web Content Accessibility Guidelines (WCAG) 2.2*: https://www.w3.org/TR/WCAG22/
- W3C WAI — *What's New in WCAG 2.2*: https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- W3C WAI — *WCAG 3 Introduction*: https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/

### Conversational / chat UI
- Nielsen Norman Group — *10 Guidelines for Designing Your Site's AI Chatbots*: https://www.nngroup.com/articles/ai-chatbots-design-guidelines/
- Nielsen Norman Group — *Designing AI Products and Features: Study Guide*: https://www.nngroup.com/articles/designing-ai-study-guide/
- Nielsen Norman Group — *Explainable AI in Chat Interfaces*: https://www.nngroup.com/articles/explainable-ai/
- Nielsen Norman Group — conversational interfaces topic hub: https://www.nngroup.com/topic/conversational-interfaces/

### Motion & interaction craft
- Emil Kowalski — personal site (animation rules referenced throughout): https://emilkowal.ski/
- Every — *Invisible Details of Interaction Design* (Rauno Freiberg): https://every.to/p/invisible-details-of-interaction-design

### Design tokens
- W3C Design Tokens Community Group — *Design Tokens specification reaches first stable version*: https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
- Tokens Studio docs — *Token Format: W3C DTCG vs Legacy*: https://docs.tokens.studio/manage-settings/token-format

### Frontend architecture
- Tailwind CSS — *Tailwind CSS v4.0* (official blog): https://tailwindcss.com/blog/tailwindcss-v4
- Tailwind Labs — GitHub releases: https://github.com/tailwindlabs/tailwindcss/releases
- shadcn/ui — changelog: https://ui.shadcn.com/docs/changelog
- Base UI: https://base-ui.com/
- Radix UI: https://www.radix-ui.com/

### Reference design systems
- Vercel — Geist design system: https://vercel.com/geist/introduction
- Vercel — Geist font: https://vercel.com/font
- Pixeldarts — *Four design principles behind Stripe, Linear, and Vercel*: https://www.pixeldarts.com/en/post/four-design-principles-behind-stripe-linear-and-vercel

### Market context (directional only, not cited for hard technical claims)
- Awwwards — winning sites archive: https://www.awwwards.com/websites/
- WebFX — *Web Design Pricing: How Much Does Web Design Cost*: https://www.webfx.com/web-design/pricing/

### Vachan project sources
- `docs/01_PRD.md`
- `docs/06_UIUX_DESIGN.md`
- `docs/12_FINAL_DECISIONS.md`
- `frontend/app/globals.css`
- `frontend/app/page.tsx`
- `frontend/app/mirror/page.tsx`
- `frontend/components/vachan/ChatBubble.tsx`
- `frontend/components/vachan/FidelityRing.tsx`
- `frontend/components/vachan/TonalitySliders.tsx`

---

> **End of document.** This wiki is a living artifact. As the product ships and learns, update each section with real user feedback, A/B results, and accessibility audit findings — and re-verify any dated technical claim (browser support, spec status) before relying on it more than ~12 months out.

