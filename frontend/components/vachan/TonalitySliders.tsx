/*
 * Tonality Sliders ("the Chameleon control") — doc 06 §6.5 #5.
 *
 * Five dials of voice. In Phase 1 two of them — Formality and Hinglish mix —
 * are LIVE: dragging them re-steers the very next reply (the backend re-prompts
 * with the new targets). Warmth and Directness are shown as MEASURED from your
 * writing; live steering for those maps to control-vector coefficients in V2,
 * so they're read-only here (honest, not a fake knob).
 */
"use client";

import styles from "./TonalitySliders.module.css";

export type Tone = {
  warmth: number;
  directness: number;
  formality: number;
  hinglish: number;
};

const ROWS: { key: keyof Tone; label: string; live: boolean; lo: string; hi: string }[] = [
  { key: "warmth", label: "Warmth", live: false, lo: "cool", hi: "warm" },
  { key: "directness", label: "Directness", live: false, lo: "gentle", hi: "blunt" },
  { key: "formality", label: "Formality", live: true, lo: "casual", hi: "formal" },
  { key: "hinglish", label: "Hinglish mix", live: true, lo: "English", hi: "heavy mix" },
];

export function TonalitySliders({
  tone,
  onChange,
  disabled,
}: {
  tone: Tone;
  onChange: (next: Tone) => void;
  disabled?: boolean;
}) {
  return (
    <div className={styles.wrap}>
      <span className="label">Tonality</span>
      {ROWS.map((row) => {
        const value = tone[row.key];
        return (
          <div className={styles.row} key={row.key}>
            <div className={styles.head}>
              <span className={styles.name}>
                {row.label}
                {row.live ? (
                  <span className={styles.liveTag}>live</span>
                ) : (
                  <span className={styles.measuredTag}>measured</span>
                )}
              </span>
              <span className={styles.val}>{Math.round(value * 100)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round(value * 100)}
              disabled={disabled || !row.live}
              aria-label={row.label}
              className={`${styles.slider} ${row.live ? "" : styles.readonly}`}
              style={{ ["--pct" as string]: `${Math.round(value * 100)}%` }}
              onChange={(e) => onChange({ ...tone, [row.key]: Number(e.target.value) / 100 })}
            />
            <div className={styles.ends}>
              <span>{row.lo}</span>
              <span>{row.hi}</span>
            </div>
          </div>
        );
      })}
      <p className={styles.note}>
        Drag <strong>Formality</strong> or <strong>Hinglish mix</strong>, then send a
        message — your clone shifts live. Warmth &amp; directness are read from your
        writing (live steering in V2).
      </p>
    </div>
  );
}
