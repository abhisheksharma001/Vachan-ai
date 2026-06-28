/*
 * Fidelity Ring ("Clone Calibration") — doc 06 §6.5 #4, the signature data-viz.
 *
 * An SVG ring fills 0–100% with the sand→coral blend; the centre shows the PFS
 * as a big number + a one-word state. Below it, thin sub-bars for the signals
 * we can honestly measure today.
 *
 * HONESTY (FD-4 / RULE 5):
 *  • The state word is band-capped — we never show "Strong/Indistinguishable"
 *    while the persona is still warming up or calibrating, no matter the score.
 *  • PFS is PROVISIONAL when a capsule has no neural fingerprint yet (judge-only
 *    basis): we flag that with a "provisional" chip and grey out the Style-match
 *    (AV-cosine) sub-bar. With a fingerprint (Slice 1.5), both light up.
 */
"use client";

import { useEffect, useRef, useState } from "react";

import styles from "./FidelityRing.module.css";

export type Fidelity = {
  pfs: number | null;
  pfs_basis?: string;
  judge_score?: number | null;
  judge_reason?: string;
  cmi_output?: number | null;
  cmi_target?: number | null;
  hard_rule_pass?: boolean;
  hard_rule_violations?: string[];
  // Slice 1.5 — the NEURAL style signals (null when no fingerprint yet).
  av_cosine?: number | null;
  centroid_distance?: number | null;
};

function stateWord(pfs: number, band?: string): string {
  if (band === "warming_up") return "Warming up";
  const byScore =
    pfs >= 0.9 ? "Indistinguishable" : pfs >= 0.8 ? "Strong" : pfs >= 0.65 ? "Good" : "Calibrating";
  // FD-4: below "stable", never overclaim — cap at "Good".
  if (band === "calibrating" && (byScore === "Indistinguishable" || byScore === "Strong")) {
    return "Good";
  }
  return byScore;
}

/** Count a number up to `target` on mount (skipped under reduced-motion). */
function useCountUp(target: number, ms = 900): number {
  const [val, setVal] = useState(0);
  const raf = useRef<number>();
  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setVal(target);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setVal(target * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target, ms]);
  return val;
}

function band(value: number): "high" | "mid" | "low" {
  return value >= 0.66 ? "high" : value >= 0.33 ? "mid" : "low";
}

function SubBar({ label, value, note }: { label: string; value: number | null; note?: string }) {
  const pct = value == null ? 0 : Math.round(value * 100);
  const tier = value == null ? "muted" : band(value);
  return (
    <div className={styles.subRow}>
      <div className={styles.subHead}>
        <span className={styles.subLabel}>{label}</span>
        <span className={styles.subVal}>{value == null ? (note ?? "—") : `${pct}%`}</span>
      </div>
      <div className={styles.track}>
        <div className={`${styles.fill} ${styles[tier]}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function FidelityRing({
  fidelity,
  band: personaBand,
  pacing,
}: {
  fidelity: Fidelity | null;
  band?: string;
  pacing?: number | null;
}) {
  const R = 78;
  const C = 2 * Math.PI * R;
  const pfs = fidelity?.pfs ?? 0;
  const animated = useCountUp(pfs);
  const offset = C * (1 - animated);

  const provisional = fidelity?.pfs_basis === "judge_only";
  const word = fidelity ? stateWord(pfs, personaBand) : "—";

  // Sub-bars from what we can measure now.
  const judge = fidelity?.judge_score != null ? fidelity.judge_score / 5 : null;
  const hinglish =
    fidelity?.cmi_output != null && fidelity?.cmi_target != null
      ? Math.max(0, 1 - Math.min(1, Math.abs(fidelity.cmi_output - fidelity.cmi_target) / 0.3))
      : null;

  return (
    <div className={styles.wrap}>
      <div className={styles.ringHead}>
        <span className="label">Clone calibration</span>
        {provisional && (
          <span className={styles.provisional} title="Full neural fingerprint lands in Slice 1.5">
            provisional
          </span>
        )}
      </div>

      <div className={styles.ringBox}>
        <svg viewBox="0 0 200 200" className={styles.svg} role="img"
             aria-label={`Fidelity ${Math.round(pfs * 100)} percent, ${word}`}>
          <defs>
            <linearGradient id="ringBlend" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F3C9A8" />
              <stop offset="100%" stopColor="#EC6A4C" />
            </linearGradient>
          </defs>
          <circle cx="100" cy="100" r={R} className={styles.ringTrack} />
          <circle
            cx="100"
            cy="100"
            r={R}
            className={styles.ringFill}
            stroke="url(#ringBlend)"
            strokeDasharray={C}
            strokeDashoffset={offset}
            transform="rotate(-90 100 100)"
          />
        </svg>
        <div className={styles.center}>
          <div className={styles.pfsNum}>{fidelity ? Math.round(animated * 100) : "—"}</div>
          <div className={styles.pfsUnit}>% fidelity</div>
          <div className={styles.word}>{word}</div>
        </div>
      </div>

      <div className={styles.subBars}>
        <SubBar label="Voice match (judge)" value={judge} />
        <SubBar label="Hinglish index" value={hinglish} />
        <SubBar label="Pacing match" value={pacing ?? null} />
        {/* Slice 1.5 — the neural style/authorship signal. Greys to "—" when the
            capsule has no fingerprint yet (PFS still judge-only). */}
        <SubBar
          label="Style match (neural)"
          value={fidelity?.av_cosine ?? null}
          note="no fingerprint"
        />
      </div>

      {fidelity?.judge_reason && (
        <p className={styles.reason}>“{fidelity.judge_reason}”</p>
      )}
      {fidelity && fidelity.hard_rule_pass === false && (
        <p className={styles.blocked}>
          Blocked by hard rules: {fidelity.hard_rule_violations?.join(", ")}
        </p>
      )}
    </div>
  );
}
