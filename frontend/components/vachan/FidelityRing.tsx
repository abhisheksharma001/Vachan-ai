/*
 * Fidelity Ring ("Clone Calibration") — doc 06 §6.5 #4.
 *
 * SVG ring filled with the sand→coral blend; centre shows PFS + one-word state.
 * Sub-bars for the signals we can honestly measure today.
 *
 * HONESTY:
 *  • State word is band-capped — never overclaim while warming/calibrating.
 *  • PFS is PROVISIONAL when the capsule has no neural fingerprint yet.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { Fidelity } from "@/lib/types";

export type { Fidelity };

function stateWord(pfs: number, band?: string): string {
  if (band === "warming_up") return "Warming up";
  const byScore =
    pfs >= 0.9 ? "Indistinguishable" : pfs >= 0.8 ? "Strong" : pfs >= 0.65 ? "Good" : "Calibrating";
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
      const eased = 1 - Math.pow(1 - t, 3);
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

function SubBar({
  label,
  value,
  note,
}: {
  label: string;
  value: number | null;
  note?: string;
}) {
  const pct = value == null ? 0 : Math.round(value * 100);
  const tier = value == null ? "muted" : band(value);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-ink-700">{label}</span>
        <span className="font-medium text-ink-900">
          {value == null ? (note ?? "—") : `${pct}%`}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-sand-200">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            tier === "high" && "bg-teal-500",
            tier === "mid" && "bg-amber-500",
            tier === "low" && "bg-coral-500",
            tier === "muted" && "bg-sand-300"
          )}
          style={{ width: `${pct}%` }}
        />
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

  const provisional = fidelity?.pfsBasis === "judge_only";
  const word = fidelity ? stateWord(pfs, personaBand) : "—";

  const judge = fidelity?.judgeScore != null ? fidelity.judgeScore / 5 : null;
  const hinglish =
    fidelity?.cmiOutput != null && fidelity?.cmiTarget != null
      ? Math.max(0, 1 - Math.min(1, Math.abs(fidelity.cmiOutput - fidelity.cmiTarget) / 0.3))
      : null;

  return (
    <div className="w-full max-w-xs space-y-5 rounded-xl border border-sand-300 bg-sand-100 p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="label">Clone calibration</span>
        {provisional && (
          <span
            className="rounded-full bg-sand-200 px-2 py-0.5 text-xs font-medium text-ink-700"
            title="Full neural fingerprint lands in Slice 1.5"
          >
            provisional
          </span>
        )}
      </div>

      <div className="relative mx-auto size-40">
        <svg
          viewBox="0 0 200 200"
          className="size-full -rotate-90"
          role="img"
          aria-label={`Fidelity ${Math.round(pfs * 100)} percent, ${word}`}
        >
          <defs>
            <linearGradient id="ringBlend" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F3C9A8" />
              <stop offset="100%" stopColor="#EC6A4C" />
            </linearGradient>
          </defs>
          <circle
            cx="100"
            cy="100"
            r={R}
            className="fill-none stroke-sand-300"
            strokeWidth="16"
          />
          <circle
            cx="100"
            cy="100"
            r={R}
            className="fill-none transition-all duration-500"
            stroke="url(#ringBlend)"
            strokeWidth="16"
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <div className="font-display text-4xl font-medium text-ink-900">
            {fidelity ? Math.round(animated * 100) : "—"}
          </div>
          <div className="text-xs text-ink-500">% fidelity</div>
          <div className="mt-1 text-sm font-medium text-coral-600">{word}</div>
        </div>
      </div>

      <div className="space-y-3">
        <SubBar label="Voice match (judge)" value={judge} />
        <SubBar label="Hinglish index" value={hinglish} />
        <SubBar label="Pacing match" value={pacing ?? null} />
        <SubBar
          label="Style match (neural)"
          value={fidelity?.avCosine ?? null}
          note="no fingerprint"
        />
      </div>

      {fidelity?.judgeReason && (
        <p className="text-sm italic text-ink-700">“{fidelity.judgeReason}”</p>
      )}
      {fidelity && fidelity.hardRulePass === false && (
        <p className="text-sm text-rose-600">
          Blocked by hard rules: {fidelity.hardRuleViolations?.join(", ")}
        </p>
      )}
    </div>
  );
}
