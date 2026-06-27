/*
 * The Mirror (doc 06 §6.6 #3) — the wow screen, now LIVE.
 *
 * Paste your writing → a clone is built (capture + capsule, server-side) →
 * chat with it while the Fidelity Ring scores every reply and the Tonality
 * Sliders let you re-steer Formality + Hinglish on the fly.
 *
 * All network calls go through same-origin /api/mirror/* route handlers, which
 * attach the dev credential server-side (see lib/backend.ts).
 */
"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { ChatBubble, TypingBubble } from "@/components/vachan/ChatBubble";
import { FidelityRing, type Fidelity } from "@/components/vachan/FidelityRing";
import { TonalitySliders, type Tone } from "@/components/vachan/TonalitySliders";
import styles from "./page.module.css";

type Phase = "paste" | "loading" | "chat";
type Msg = { role: "user" | "clone"; content: string };

const SAMPLE = `haan bhai bilkul ho jayega, tension mat le
scene yeh hai ki frontend pe thoda kaam baaki hai abhi
yaar kal tak deploy kar dunga, 10 baje tak update bhej deta hu
nice work btw, client khush ho jayega isse`;

const clamp01 = (n: number) => Math.max(0, Math.min(1, n));

const BAND_LABEL: Record<string, string> = {
  warming_up: "warming up",
  calibrating: "calibrating",
  stable: "stable",
};

export default function MirrorPage() {
  const [phase, setPhase] = useState<Phase>("paste");
  const [paste, setPaste] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [personaId, setPersonaId] = useState<string | null>(null);
  const [band, setBand] = useState<string>("warming_up");
  const [avgWords, setAvgWords] = useState<number>(12);
  const [tone, setTone] = useState<Tone>({
    warmth: 0.6,
    directness: 0.5,
    formality: 0.4,
    hinglish: 0.3,
  });

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [fidelity, setFidelity] = useState<Fidelity | null>(null);
  const [pacing, setPacing] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function buildClone() {
    if (paste.trim().length < 20) {
      setError("Paste a little more — a few of your real messages work best.");
      return;
    }
    setError(null);
    setPhase("loading");
    try {
      const res = await fetch("/api/mirror/capture", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: paste, sourceType: "paste" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Capture failed.");

      setPersonaId(data.personaId);
      setBand(data.band ?? "warming_up");
      setAvgWords(Number(data.style?.avg_message_tokens) || 12);

      const cap = data.capsuleData;
      if (cap) {
        setTone({
          warmth: clamp01((cap.steering?.warmth ?? 1.2) / 2),
          directness: clamp01((cap.steering?.directness ?? 1.0) / 2),
          formality: clamp01(cap.language?.formality_target ?? 0.4),
          hinglish: clamp01(cap.language?.cmi_target ?? 0.3),
        });
      }
      setMessages([
        {
          role: "clone",
          content: "ho gaya! ab main tere style mein baat karunga — kuch bhi pooch le 👇",
        },
      ]);
      setPhase("chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setPhase("paste");
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || sending || !personaId) return;
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    setError(null);
    requestAnimationFrame(() => scrollRef.current?.scrollTo(0, 1e6));
    try {
      const res = await fetch("/api/mirror/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          personaId,
          message: text,
          history,
          tone: { formality: tone.formality, hinglish: tone.hinglish },
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Your clone could not reply.");

      setMessages((prev) => [...prev, { role: "clone", content: data.reply }]);
      if (data.fidelity) setFidelity(data.fidelity as Fidelity);
      if (data.band) setBand(data.band);
      // Pacing proxy: reply length vs the persona's measured message length.
      const words = String(data.reply).trim().split(/\s+/).length;
      setPacing(clamp01(1 - Math.min(1, Math.abs(words - avgWords) / Math.max(avgWords, 1))));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSending(false);
      requestAnimationFrame(() => scrollRef.current?.scrollTo(0, 1e6));
    }
  }

  return (
    <main className={styles.page}>
      <nav className={styles.nav}>
        <Link href="/" className={styles.wordmark}>
          Vachan<span>.</span>ai
        </Link>
        <span className="chip">The Mirror · Phase 1</span>
      </nav>

      {phase !== "chat" ? (
        <section className={styles.intro}>
          <div className={styles.introEyebrow}>The Mirror</div>
          <h1 className={styles.introTitle}>Paste your writing. Meet your clone.</h1>
          <p className={styles.introSub}>
            Drop in a few of your real messages (Hinglish welcome). We sanitize PII
            locally, measure your voice, and you can chat with a clone that sounds
            like you — scored live.
          </p>

          <div className={styles.pasteCard}>
            <textarea
              className={styles.textarea}
              placeholder="haan bhai, isko aise karte hain… (paste a few of your real messages)"
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              rows={8}
              disabled={phase === "loading"}
            />
            <div className={styles.pasteActions}>
              <button
                type="button"
                className={styles.sampleBtn}
                onClick={() => setPaste(SAMPLE)}
                disabled={phase === "loading"}
              >
                Use a sample
              </button>
              <Button variant="primary" onClick={buildClone} disabled={phase === "loading"}>
                {phase === "loading" ? "Building your clone…" : "Create my clone"}
              </Button>
            </div>
            <p className={styles.privacy}>
              🔒 Phone numbers, UPI IDs, emails and the like are redacted before
              anything is stored — only a hash of the sanitized text is kept.
            </p>
            {error && <p className={styles.error}>{error}</p>}
          </div>
        </section>
      ) : (
        <section className={styles.mirror}>
          {/* chat column */}
          <div className={styles.chatPanel}>
            <div className={styles.chatHeader}>
              <div className={styles.avatar} />
              <div className={styles.chatTitle}>Your clone</div>
              <span className={`chip ${styles.bandChip}`}>
                <span className={`${styles.dot} ${styles[band] ?? ""}`} />
                {BAND_LABEL[band] ?? band}
              </span>
            </div>
            <div className={styles.chatBody} ref={scrollRef}>
              {messages.map((m, i) => (
                <ChatBubble key={i} author={m.role}>
                  {m.content}
                </ChatBubble>
              ))}
              {sending && <TypingBubble />}
            </div>
            <div className={styles.composer}>
              <input
                className={styles.input}
                placeholder="bhai project kaisa chal raha hai?"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                disabled={sending}
              />
              <Button variant="primary" onClick={send} disabled={sending || !input.trim()}>
                Send
              </Button>
            </div>
            {error && <p className={styles.error}>{error}</p>}
          </div>

          {/* calibration column */}
          <aside className={styles.sidePanel}>
            <FidelityRing fidelity={fidelity} band={band} pacing={pacing} />
            <div className={styles.divider} />
            <TonalitySliders tone={tone} onChange={setTone} disabled={sending} />
          </aside>
        </section>
      )}
    </main>
  );
}
