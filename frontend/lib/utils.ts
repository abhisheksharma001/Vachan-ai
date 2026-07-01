import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind utility classes. clsx handles conditional arrays;
 * tailwind-merge deduplicates conflicting utilities.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a 0..1 number as a percentage string. */
export function formatPercent(n: number | null | undefined, fallback = "—"): string {
  if (n == null || Number.isNaN(n)) return fallback;
  return `${Math.round(Math.max(0, Math.min(1, n)) * 100)}%`;
}

/** Map word count to the FD-4 cold-start band key. */
export function bandFromWords(words: number): "warming_up" | "calibrating" | "stable" {
  if (words < 700) return "warming_up";
  if (words <= 10_000) return "calibrating";
  return "stable";
}

/** Map word count to a human-friendly band label. */
export function bandLabel(words: number): string {
  if (words < 700) return "Warming up — starting cautious";
  if (words <= 10_000) return "Calibrating — good start";
  return "Stable — high confidence";
}

/** Map band key to a short display label. */
export function bandShortLabel(band: string): string {
  switch (band) {
    case "warming_up":
      return "warming up";
    case "calibrating":
      return "calibrating";
    case "stable":
      return "stable";
    default:
      return band;
  }
}
