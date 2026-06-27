/*
 * Phase 0 showcase — the design-system shell made visible.
 *
 * This page proves the Sandy + Coral language (doc 06) is real: the hero
 * (§6.6 #1), the live tokens (§6.2), the base components (§6.5 #1–3), and a
 * static Mirror preview that demonstrates the SAME PII redaction the backend
 * pipeline performs (a phone number becomes [IN_PHONE] before it's ever shown).
 *
 * The LIVE Mirror — wired to POST /messages with the Fidelity Ring + sliders —
 * is Phase 1 (doc 06 §6.6 #3). We keep the phase boundary clean on purpose.
 */
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import buttonStyles from "@/components/ui/Button.module.css";
import { Card } from "@/components/ui/Card";
import { ChatBubble, TypingBubble } from "@/components/vachan/ChatBubble";
import styles from "./page.module.css";

const PALETTE: { name: string; varName: string; hex: string }[] = [
  { name: "sand-50", varName: "--sand-50", hex: "#FBF7F1" },
  { name: "sand-100", varName: "--sand-100", hex: "#F6EEE3" },
  { name: "sand-300", varName: "--sand-300", hex: "#E4D2BC" },
  { name: "coral-500", varName: "--coral-500", hex: "#EC6A4C" },
  { name: "coral-700", varName: "--coral-700", hex: "#B23D2C" },
  { name: "ink-900", varName: "--ink-900", hex: "#2C211A" },
  { name: "teal-500", varName: "--teal-500", hex: "#2F8F83" },
  { name: "amber-500", varName: "--amber-500", hex: "#C9852A" },
];

export default function Home() {
  return (
    <main className={styles.page}>
      {/* nav */}
      <nav className={styles.nav}>
        <div className={styles.wordmark}>
          Vachan<span>.</span>ai
        </div>
        <Link href="/mirror" className={`${buttonStyles.btn} ${buttonStyles.ghost}`}>
          Open the Mirror →
        </Link>
      </nav>

      {/* hero (§6.6 #1) */}
      <header className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroEyebrow}>The Tone Engine</div>
          <h1 className={styles.heroTitle}>Every agent. Your voice.</h1>
          <p className={styles.heroSub}>
            Vachan.ai clones how <em>you</em> communicate — your warmth, your
            pacing, your Hinglish — so every automated reply still sounds
            unmistakably like you.
          </p>
          <div className={styles.heroActions}>
            <Link href="/mirror" className={`${buttonStyles.btn} ${buttonStyles.primary}`}>
              Paste your writing
            </Link>
            <a href="#mirror-preview" className={`${buttonStyles.btn} ${buttonStyles.secondary}`}>
              See how it works
            </a>
          </div>
        </div>
      </header>

      {/* palette (§6.2) */}
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h2>The palette</h2>
          <p>
            Warm sand canvas, coral as the precious accent — “the voice.” Every
            color is a CSS token; nothing is hardcoded.
          </p>
        </div>
        <div className={styles.swatches}>
          {PALETTE.map((c) => (
            <div className={styles.swatch} key={c.name}>
              <div
                className={styles.swatchColor}
                style={{ background: `var(${c.varName})` }}
              />
              <div className={styles.swatchMeta}>
                <div className={styles.swatchName}>{c.name}</div>
                <div className={styles.swatchHex}>{c.hex}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* buttons (§6.5 #1) */}
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h2>Buttons</h2>
          <p>Primary coral, sand secondary, ghost — each with hover, active and disabled states.</p>
        </div>
        <div className={styles.row}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="primary" disabled>
            Disabled
          </Button>
        </div>
      </section>

      {/* cards (§6.5 #2) */}
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h2>Cards</h2>
          <p>Sand surface, soft warm shadow. Interactive cards lift on hover.</p>
        </div>
        <div className={styles.grid}>
          <Card>
            <h3>Persona</h3>
            <p style={{ marginTop: 8 }}>
              A named communication identity. One person can own several.
            </p>
          </Card>
          <Card interactive>
            <h3>Fidelity</h3>
            <p style={{ marginTop: 8 }}>
              How close a reply sounds to you. The Fidelity Ring lands in Phase 1.
            </p>
          </Card>
          <Card>
            <h3>Privacy</h3>
            <p style={{ marginTop: 8 }}>
              PII is scrubbed before anything is stored or sent to a model.
            </p>
          </Card>
        </div>
      </section>

      {/* the Mirror preview (§6.5 #3 + §6.6 #3, static) */}
      <section className={styles.section} id="mirror-preview">
        <div className={styles.sectionHead}>
          <h2>The Mirror — preview</h2>
          <p>
            Coral bubbles are the clone (“the voice”); sand bubbles are you. This
            preview shows the <strong>real</strong> privacy behavior: the phone
            number is redacted to <code>[IN_PHONE]</code> before it’s ever shown
            — exactly what the backend pipeline does.
          </p>
        </div>
        <div className={styles.mirrorWrap}>
          <div className={styles.mirrorPanel}>
            <div className={styles.mirrorHeader}>
              <div className={styles.avatar} />
              <div className={styles.mirrorTitle}>Your clone</div>
              <span
                className="chip"
                style={{ marginLeft: "auto", fontSize: 12 }}
              >
                warming up
              </span>
            </div>
            <div className={styles.mirrorBody}>
              <ChatBubble author="user">
                hey can you reply to clients for me?
              </ChatBubble>
              <ChatBubble author="clone">
                haan bilkul! main aapke tone mein reply karunga 🙌
              </ChatBubble>
              <ChatBubble author="user">
                cool. tell them to call me at +91 98765 43210
              </ChatBubble>
              <ChatBubble author="clone">
                got it — I’ll share{" "}
                <span className={styles.pii}>[IN_PHONE]</span> with them. (your
                number is redacted before storage)
              </ChatBubble>
              <TypingBubble />
            </div>
          </div>
          <p className={styles.mirrorNote}>
            This is a static preview. The{" "}
            <Link href="/mirror">live Mirror</Link> — wired to the real capture +
            chat pipeline with the Fidelity Ring and Tonality Sliders — is ready.{" "}
            <Link href="/mirror">Paste your writing →</Link>
          </p>
        </div>
      </section>

      <footer className={styles.footer}>
        Vachan.ai · Phase 0 foundation · Sandy + Coral design system (doc 06).
      </footer>
    </main>
  );
}
