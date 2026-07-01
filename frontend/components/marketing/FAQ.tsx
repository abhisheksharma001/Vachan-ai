"use client";

import { useState } from "react";
import styles from "./FAQ.module.css";

const ITEMS = [
  {
    q: "What writing should I paste?",
    a: "Anything you wrote: emails, DMs, Slack messages, notes. The more representative your samples, the closer the clone sounds to you. We redact phone numbers, UPI IDs, emails, and other private details before storage.",
  },
  {
    q: "Is my data private?",
    a: "Yes. Private information is sanitized locally using Presidio + Indian-pattern detectors before anything is stored. Only redacted text and derived voice signals are kept.",
  },
  {
    q: "Does Vachan work in Hinglish?",
    a: "Hinglish is a first-class language here. The system detects code-switching automatically and can steer between English, Hindi, and mixed registers.",
  },
  {
    q: "Can I use this with my existing AI agent?",
    a: "Yes. Vachan exposes an MCP live-mount and a signed Capsule Export Bundle for voice platforms like Vapi, Retell, and LiveKit.",
  },
  {
    q: "What does 'fidelity' mean?",
    a: "Fidelity measures how close a generated reply sounds to your real voice. It is composite, calibrated against humans, and honest about provisional scores while your capsule is still warming up.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<string | null>(ITEMS[0].q);

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>
        Frequently asked questions
      </h2>
      <div className={styles.list} role="list">
        {ITEMS.map((item) => (
          <div key={item.q} className={styles.item} role="listitem">
            <button
              type="button"
              className={styles.question}
              onClick={() => setOpen(open === item.q ? null : item.q)}
              aria-expanded={open === item.q}
            >
              {item.q}
              <span className={styles.icon} aria-hidden="true">
                {open === item.q ? "−" : "+"}
              </span>
            </button>
            {open === item.q && <p className={styles.answer}>{item.a}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
