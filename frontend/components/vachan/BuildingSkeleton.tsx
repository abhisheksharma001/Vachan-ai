"use client";

import { useEffect, useState } from "react";
import { bandFromWords, bandLabel } from "@/lib/utils";
import styles from "./BuildingSkeleton.module.css";

const STEPS = [
  "Scanning for private details…",
  "Extracting your style — words, pacing, Hinglish mix…",
  "Building your Persona Capsule…",
  "Opening the Mirror…",
];

export function BuildingSkeleton({ wordCount }: { wordCount: number }) {
  const [step, setStep] = useState(0);
  const band = bandFromWords(wordCount);
  const predicted = bandLabel(wordCount).split(" —")[0];

  useEffect(() => {
    if (step >= STEPS.length - 1) return;
    const t = setTimeout(() => setStep((s) => s + 1), 4500);
    return () => clearTimeout(t);
  }, [step]);

  return (
    <div className={styles.outer} role="status" aria-live="polite" aria-label="Building your clone">
      <div className={styles.card}>
        <div className={styles.shimmer} />
        <div className={styles.content}>
          <h2 className={styles.title}>Building your clone…</h2>
          <p className={styles.step}>{STEPS[step]}</p>
          <div className={styles.track}>
            <div
              className={styles.bar}
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
          <p className={styles.hint}>
            This takes 10–60 seconds depending on how much you shared.
          </p>
          <div className={styles.band}>
            <span className="chip">
              Predicted band: <strong>{predicted.toLowerCase()}</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
