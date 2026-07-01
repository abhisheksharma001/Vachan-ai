"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PrivacyBadge } from "@/components/vachan/PrivacyBadge";
import { BuildingSkeleton } from "@/components/vachan/BuildingSkeleton";
import { LiveRegion } from "@/components/a11y/LiveRegion";
import { bandLabel } from "@/lib/utils";
import styles from "./page.module.css";

type Method = "paste" | "whatsapp" | "manual";
type Phase = "input" | "preview" | "building" | "chat";

const SAMPLE = `haan bhai bilkul ho jayega, tension mat le
scene yeh hai ki frontend pe thoda kaam baaki hai abhi
yaar kal tak deploy kar dunga, 10 baje tak update bhej deta hu
nice work btw, client khush ho jayega isse`;

const METHODS: { id: Method; title: string; body: string }[] = [
  { id: "paste", title: "Paste your writing", body: "Notes, DMs, emails — anything you wrote." },
  { id: "whatsapp", title: "Upload WhatsApp export", body: "Export a chat without media for richer signal." },
  { id: "manual", title: "Build it manually", body: "Answer a few questions for a starter voice." },
];

export default function CapturePage() {
  const router = useRouter();
  const [method, setMethod] = useState<Method>("paste");
  const [paste, setPaste] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("input");
  const [preview, setPreview] = useState<{ sanitized: string; entities: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announce, setAnnounce] = useState("");

  const words = paste.trim() ? paste.trim().split(/\s+/).length : 0;

  async function previewSanitization() {
    if (words < 10) {
      setError("Paste a little more — a few of your real messages work best.");
      return;
    }
    setError(null);
    setPhase("preview");
    setAnnounce("Previewing redacted text");
    const res = await fetch("/api/capture/preview", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: paste, sourceType: method }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error ?? "Could not preview sanitization.");
      setPhase("input");
      return;
    }
    setPreview({ sanitized: data.sanitized, entities: data.entities ?? [] });
  }

  async function buildClone() {
    setPhase("building");
    setAnnounce("Building your clone");
    try {
      const res = await fetch("/api/capture/build", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: paste, sourceType: method }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Build failed.");
      router.push(`/mirror?personaId=${data.personaId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setPhase("input");
    }
  }

  if (phase === "building") {
    return (
      <div className={styles.page}>
        <nav className={styles.nav}>
          <Link href="/" className={styles.wordmark}>
            Vachan<span>.</span>ai
          </Link>
        </nav>
        <BuildingSkeleton wordCount={words} />
        <LiveRegion message={announce} />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <Link href="/" className={styles.wordmark}>
          Vachan<span>.</span>ai
        </Link>
      </nav>

      <main className={styles.main}>
        <header className={styles.header}>
          <h1 className={styles.title}>How should Vachan learn your voice?</h1>
          <p className={styles.lead}>
            A few real messages are enough. We scrub the private stuff before it ever reaches us.
          </p>
        </header>

        <div className={styles.methods} role="tablist" aria-label="Capture method">
          {METHODS.map((m) => (
            <Card
              key={m.id}
              interactive
              className={`${styles.methodCard} ${method === m.id ? styles.selected : ""}`}
              onClick={() => setMethod(m.id)}
              role="tab"
              aria-selected={method === m.id}
            >
              <h3 className={styles.methodTitle}>{m.title}</h3>
              <p className={styles.methodBody}>{m.body}</p>
            </Card>
          ))}
        </div>

        <Card className={styles.formCard}>
          {method === "paste" ? (
            <>
              <label htmlFor="paste" className="label">
                Your writing
              </label>
              <textarea
                id="paste"
                className={styles.textarea}
                placeholder="haan bhai, isko aise karte hain… (paste a few of your real messages)"
                rows={8}
                value={paste}
                onChange={(e) => setPaste(e.target.value)}
              />
              <div className={styles.metaRow}>
                <span>{words.toLocaleString()} words</span>
                <span className={styles.band}>{bandLabel(words)}</span>
              </div>
            </>
          ) : method === "whatsapp" ? (
            <>
              <label htmlFor="file" className="label">
                WhatsApp export
              </label>
              <input
                id="file"
                type="file"
                accept=".txt,.zip"
                className={styles.fileInput}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <p className={styles.hint}>
                WhatsApp → Settings → Chats → Chat history → Export chat → Without media.
              </p>
              {file && <p className={styles.fileName}>{file.name}</p>}
            </>
          ) : (
            <p className={styles.hint}>Manual builder placeholder — sliders + do/don’t chips.</p>
          )}

          <div className={styles.actions}>
            {method === "paste" && (
              <Button variant="secondary" onClick={() => setPaste(SAMPLE)}>
                Try a sample
              </Button>
            )}
            <Button
              variant="primary"
              disabled={method === "paste" ? words < 10 : !file}
              onClick={method === "paste" ? previewSanitization : buildClone}
            >
              {method === "paste" ? "Check & build my clone" : "Use these messages"}
            </Button>
          </div>

          <PrivacyBadge entityCount={preview?.entities.length} />

          {phase === "preview" && preview && (
            <div className={styles.previewBox}>
              <div className="label">What we keep after redaction</div>
              <pre className={styles.previewPre}>
                {preview.sanitized}
              </pre>
              <div className={styles.entities}>
                {preview.entities.map((e) => (
                  <span key={e} className="chip">
                    {e}
                  </span>
                ))}
              </div>
              <div className={styles.actions}>
                <Button variant="secondary" onClick={() => setPhase("input")}>
                  Edit text
                </Button>
                <Button variant="primary" onClick={buildClone}>
                  Build my clone
                </Button>
              </div>
            </div>
          )}

          {error && (
            <div className={styles.error} role="alert">
              {error}
            </div>
          )}
        </Card>
      </main>

      <LiveRegion message={announce} />
    </div>
  );
}
