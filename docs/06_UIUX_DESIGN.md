# 06 — UI/UX Design System (Sandy + Coral)

> Abhishek asked me (the architect) to **design this myself** and hand Sonnet **exact, step-by-step** instructions. So this file is prescriptive: copy the tokens, follow the component specs, don't improvise the visual language. Sonnet: build *exactly* this. If a spec is ambiguous, STOP and ask (RULE 1) — do not invent a different palette or layout.
>
> Goal feel: **premium boutique studio tool**, warm, calm, India-proud, world-class — *not* a generic SaaS dashboard. Sandy canvas, coral as the living accent (it's the "voice"/warmth of the product).

---

## 6.1 Design principles (the 6 rules that make it feel expensive)
1. **Warm neutrals, not gray.** The whole canvas is sandy/cream. Never pure white (`#fff`) backgrounds, never cold gray. Warmth = the brand.
2. **Coral is precious — use it sparingly.** Coral is the accent for *the voice itself*: the clone's bubbles, the fidelity ring, primary actions. If everything is coral, nothing is. ~10% coral, ~90% sand.
3. **Generous space.** Big margins, airy line-height, one idea per section. Cramped = cheap.
4. **Few weights, strong contrast.** A serif display for headings + a clean sans for body. Large headings, comfortable body, no tiny gray mush.
5. **Soft, low, warm shadows.** Shadows are warm-tinted and subtle (never harsh black drop-shadows).
6. **Calm motion.** Gentle ease, short durations. Motion confirms; it never distracts (see `06.7`).

---

## 6.2 Color tokens (the exact palette — use these CSS variables everywhere)

Define once as CSS custom properties (and mirror into the Tailwind config). **Never hardcode hex in components — always use the token.**

```css
:root {
  /* ── SAND (canvas & surfaces) ── */
  --sand-50:  #FBF7F1;   /* lightest cream — page background */
  --sand-100: #F6EEE3;   /* default surface / cards */
  --sand-200: #EFE2D2;   /* raised surface, hover fill */
  --sand-300: #E4D2BC;   /* borders, dividers */
  --sand-400: #D2B896;   /* muted lines, disabled */
  --sand-500: #B9966B;   /* deep sand / secondary text on light */

  /* ── CORAL (the accent = "the voice") ── */
  --coral-300: #F6A98E;  /* soft coral — light fills, highlights */
  --coral-400: #F08A6B;  /* coral — secondary accents */
  --coral-500: #EC6A4C;  /* PRIMARY coral — buttons, clone bubbles, ring */
  --coral-600: #D7503A;  /* hover/pressed coral */
  --coral-700: #B23D2C;  /* deep coral — text on sand when needed */

  /* ── CORAL-SAND BLEND (the signature gradient) ── */
  --blend-warm: linear-gradient(135deg, #F3C9A8 0%, #EC6A4C 100%); /* sand→coral hero wash */
  --blend-soft: linear-gradient(135deg, #F6EEE3 0%, #F6A98E 100%); /* subtle card wash */

  /* ── INK (text) ── */
  --ink-900: #2C211A;    /* primary text — warm near-black (NOT pure black) */
  --ink-700: #5A4A3D;    /* secondary text */
  --ink-500: #8A7563;    /* tertiary / captions */

  /* ── SUPPORT / SEMANTIC ── */
  --teal-500:  #2F8F83;  /* success / "on-voice" / fidelity good (cool foil to coral) */
  --amber-500: #C9852A;  /* warning / "drifting" / needs attention */
  --rose-600:  #B23D52;  /* error / "off-voice" / blocked */

  /* ── SHADOWS (warm, soft) ── */
  --shadow-sm: 0 1px 2px rgba(78, 52, 34, 0.06);
  --shadow-md: 0 6px 20px rgba(78, 52, 34, 0.10);
  --shadow-lg: 0 18px 50px rgba(78, 52, 34, 0.14);

  /* ── RADII ── */
  --radius-sm: 10px;  --radius-md: 16px;  --radius-lg: 24px;  --radius-pill: 999px;
}
```

**Dark mode (optional, V1+):** invert to a warm dark — `--ink-900` becomes a deep espresso `#241B15` canvas, sand surfaces become `#33271E`, coral stays the accent. Don't ship dark mode in Phase 1 unless asked.

**Usage rules (memorize):**
- Page bg = `--sand-50`. Cards = `--sand-100` with `--sand-300` 1px border + `--shadow-sm`.
- **Clone/AI message bubbles = coral** (`--coral-500` bg, white-ish `--sand-50` text). **User message bubbles = sand** (`--sand-200`, `--ink-900` text). This makes "the voice" literally the coral one.
- Primary button = `--coral-500` → hover `--coral-600`. Secondary = sand surface + `--sand-300` border.
- Success/"on-voice" = teal, "drifting" = amber, "off-voice/blocked" = rose. (Coral is brand, not "success" — keep them distinct.)

---

## 6.3 Typography
- **Display / headings:** a warm humanist serif — **Fraunces** (variable, characterful) or **Instrument Serif**. Used for H1–H3, big numbers (fidelity %), and the wordmark.
- **Body / UI:** a clean neutral sans — **Inter** or **Geist**. Used for paragraphs, labels, buttons, data.
- **Mono (capsule/code views):** **JetBrains Mono** or **Geist Mono** — for the YAML capsule editor and any code.

```
H1  Fraunces  44–60px  / 1.05 / weight 500  / --ink-900
H2  Fraunces  30–36px  / 1.1  / weight 500
H3  Fraunces  22–24px  / 1.2
Body Inter    16–18px  / 1.6  / --ink-700 (use 18 for reading comfort)
Label Inter   13–14px  / 1.4  / weight 500 / --ink-500 / letter-spacing 0.02em
Button Inter  15px     / weight 600
Mono JetBrains 14px    / 1.5
```
Get fonts from Google Fonts / Fontshare (Fraunces, Instrument Serif, Inter are all free). Self-host via `next/font` for performance.

---

## 6.4 Spacing, layout, grid
- **Spacing scale (4px base):** 4, 8, 12, 16, 24, 32, 48, 64, 96. Use generously — default section padding ≥ 48px.
- **Max content width:** 1200px centered; reading columns ≤ 680px.
- **Grid:** 12-col with 24px gutters on desktop; single column on mobile.
- **Bento layout** for the dashboard (asymmetric cards of different sizes) — feels editorial, not gridlocked.

---

## 6.5 Core components (build these as reusable shadcn/ui-based components)

For each: what it is, tokens, states. Sonnet — implement each as a typed React component in `components/ui/` or `components/vachan/`.

1. **Button**
   - Primary: bg `--coral-500`, text `--sand-50`, radius `--radius-pill`, padding `12px 22px`, `--shadow-sm`; hover bg `--coral-600` + lift 1px; active: no lift; disabled: `--sand-400` bg, no shadow.
   - Secondary: bg `--sand-100`, border 1px `--sand-300`, text `--ink-900`; hover bg `--sand-200`.
   - Ghost: transparent, text `--coral-600`; hover bg `--coral-300`/20%.

2. **Card / Surface** — bg `--sand-100`, border 1px `--sand-300`, radius `--radius-md`, `--shadow-sm`; on hover (if interactive) `--shadow-md` + 1px lift.

3. **Chat bubble** (the heart of The Mirror)
   - Clone/AI: bg `--coral-500`, text `--sand-50`, radius `--radius-lg` with one squared corner (bottom-left), max-width 78%, aligned left.
   - User: bg `--sand-200`, text `--ink-900`, squared bottom-right, aligned right.
   - Typing indicator: three `--sand-50` dots pulsing inside a coral bubble (mimics the human-pacing delay from `01` §1.6).

4. **Fidelity Ring ("Clone Calibration")** — the signature data-viz.
   - A circular ring (SVG) filling 0–100%, stroke = `--blend-warm` gradient (sand→coral). Center shows the **PFS** big number (Fraunces, `--ink-900`) + a one-word state: "Indistinguishable / Strong / Good / Calibrating".
   - Below: 3 thin sub-bars — *Vocabulary match*, *Pacing match*, *Hinglish index* — each a small labeled progress bar (teal when high, amber when mid).
   - Gamified microcopy: *"Level 3 → complete today's prompt to reach Level 4 (Indistinguishable)."*

5. **Tonality Slider** (the Chameleon control)
   - Horizontal sliders for **Warmth · Directness · Humor · Formality · Hinglish mix**. Track = `--sand-300`, filled portion = `--blend-warm`, thumb = `--coral-500` with `--shadow-md`.
   - Live preview: as the user drags, re-render a sample reply so they *feel* the change. (Phase 1: re-prompt with updated constraints; V2: this maps to steering coefficients.)

6. **Persona Capsule editor** — split view: left = friendly form (sliders, do/don't chips, language mix); right = the live `persona.md` (mono, read-only in Phase 1, editable later). Shows `version`, `confidence`, `evidence_tokens` as small pills.

7. **Ghostwriter approval card** — for the queue: shows the incoming message, the drafted in-voice reply (in a coral bubble), the fidelity score, and two big buttons: **Send** (coral primary) / **Edit**. Sensitive-topic badge (amber) if flagged.

8. **Version history timeline** — vertical timeline of capsule commits; each node shows the **semantic diff** in plain English ("Hinglish 29%→35%, formality 0.62→0.49, added 'scene kya hai'"). A **Rollback** ghost button per node.

9. **Channel connector grid** — cards for Web/WhatsApp/Telegram/Slack/etc., each with a connect state (Connected = teal dot, Setup needed = amber). WhatsApp card includes the "verification concierge" step (`09`).

10. **Empty / loading / error states** — never blank. Empty = a warm illustration + one line of guidance. Loading = a soft coral shimmer on sand. Error = rose, plain-English message + a next step (never a raw stack trace to the user).

---

## 6.6 Key screens (what to build, in order)

1. **Landing / hero** — big Fraunces headline over a `--blend-warm` wash; one line: *"Every agent. Your voice."* One coral CTA. Sparse, confident.
2. **Onboarding capture** — three big choices: *Paste your writing · Upload WhatsApp export · Build it manually.* Reassuring privacy line ("your data is sanitized locally first — `09`").
3. **The Mirror (sandbox chat)** — the wow screen: chat with your clone; Fidelity Ring in a side panel updating live; sliders to tweak.
4. **Dashboard (bento)** — personas, fidelity scores, recent conversations, drift alerts, connected channels.
5. **Persona detail** — capsule editor + version timeline + fidelity breakdown.
6. **Approval queue** — Ghostwriter cards.
7. **Channels** — connector grid.
8. **(Vande Bharatam demo mode)** — a themed variant of The Mirror with the three mentor agents (see `11`).

---

## 6.7 Motion (calm, purposeful)
- Durations: 150–250ms for UI feedback; 400–600ms for entrance.
- Easing: `cubic-bezier(0.22, 1, 0.36, 1)` (gentle ease-out) for entrances; standard ease for hovers.
- Use sparingly: button hover lift, card hover shadow, fidelity ring counts up on load, chat bubbles fade+rise in, slider live-preview cross-fades. **Respect `prefers-reduced-motion`** — disable non-essential motion.
- Library: **Framer Motion** (React) or GSAP if a scroll-driven landing is wanted. Don't over-animate the dashboard.

---

## 6.8 Accessibility (non-negotiable)
- Contrast: body text `--ink-700`/`--ink-900` on sand passes WCAG AA. **Check coral-on-sand and white-on-coral for AA** — if a pairing fails, darken to `--coral-600`/`--coral-700`. (If unsure, STOP and verify with a contrast checker — RULE 1.)
- Full keyboard nav, visible focus rings (coral, 2px offset), proper ARIA on chat/sliders/dialogs.
- Don't encode meaning in color alone — pair the teal/amber/rose states with an icon + label.

---

## 6.9 Handoff checklist for Sonnet
- [ ] Tokens (§6.2) in `globals.css` + Tailwind config — no hardcoded hex anywhere.
- [ ] Fonts wired via `next/font` (Fraunces + Inter + JetBrains Mono).
- [ ] Components from §6.5 built, typed, with all states (default/hover/active/disabled/loading/error).
- [ ] Screens from §6.6 built in order; web Mirror first.
- [ ] Motion per §6.7 with reduced-motion fallback.
- [ ] A11y per §6.8 verified, not assumed.
- [ ] Anything visual you weren't sure about → asked Abhishek, didn't improvise (RULE 1).
