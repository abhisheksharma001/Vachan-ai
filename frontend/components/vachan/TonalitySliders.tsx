/*
 * Tonality Sliders ("the Chameleon control") — doc 06 §6.5 #5.
 *
 * Formality and Hinglish mix are LIVE: dragging them re-steers the next reply.
 * Warmth and Directness are MEASURED from the writing and read-only here.
 */
"use client";

import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import type { Tone } from "@/lib/types";

export type { Tone };

const ROWS: {
  key: keyof Tone;
  label: string;
  live: boolean;
  lo: string;
  hi: string;
}[] = [
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
    <div className="w-full max-w-xs space-y-5 rounded-xl border border-sand-300 bg-sand-100 p-5 shadow-sm">
      <span className="label">Tonality</span>
      {ROWS.map((row) => {
        const value = tone[row.key];
        const numeric = Math.round(value * 100);
        return (
          <div className="space-y-2" key={row.key}>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-ink-900">
                {row.label}
                {row.live ? (
                  <span className="rounded-full bg-coral-500 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sand-50">
                    live
                  </span>
                ) : (
                  <span className="rounded-full bg-sand-200 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-700">
                    measured
                  </span>
                )}
              </span>
              <span className="text-sm font-medium text-ink-900">{numeric}</span>
            </div>
            <Slider
              value={[numeric]}
              min={0}
              max={100}
              disabled={disabled || !row.live}
              aria-label={row.label}
              onValueChange={(value) => {
                const next = Array.isArray(value) ? value[0] : value;
                if (typeof next === "number") {
                  onChange({ ...tone, [row.key]: next / 100 });
                }
              }}
            />
            <div className="flex justify-between text-xs text-ink-500">
              <span>{row.lo}</span>
              <span>{row.hi}</span>
            </div>
          </div>
        );
      })}
      <p className="text-xs leading-relaxed text-ink-700">
        Drag <strong>Formality</strong> or <strong>Hinglish mix</strong>, then send a
        message — your clone shifts live. Warmth &amp; directness are read from your
        writing (live steering in V2).
      </p>
    </div>
  );
}
