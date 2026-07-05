"use client";

import { cn } from "@/lib/utils";

type Author = "user" | "clone";

export type Message = {
  role: Author;
  content: string;
  timestamp?: string;
};

export function ChatBubble({
  author,
  isCorrection,
  children,
  timestamp,
}: {
  author: Author;
  isCorrection?: boolean;
  children: React.ReactNode;
  timestamp?: string;
}) {
  const isClone = author === "clone";
  return (
    <div
      className={cn(
        "flex w-full",
        isClone ? "justify-start" : "justify-end"
      )}
    >
      <div
        className={cn(
          "max-w-[85%] px-4 py-2.5 text-[15px] leading-relaxed sm:max-w-[75%]",
          isClone
            ? "rounded-2xl rounded-bl-none bg-coral-500 text-sand-50"
            : isCorrection
              ? "rounded-2xl rounded-br-none border-2 border-dashed border-amber-400 bg-amber-50 text-ink-900"
              : "rounded-2xl rounded-br-none bg-sand-200 text-ink-900"
        )}
      >
        {isCorrection && (
          <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-amber-700">
            Correction
          </span>
        )}
        {children}
        {timestamp && (
          <time
            dateTime={timestamp}
            className="mt-1 block text-[11px] opacity-60"
          >
            {formatBubbleTime(timestamp)}
          </time>
        )}
      </div>
    </div>
  );
}

/** Human-readable time for the bubble label; falls back to the raw string
 * when the value isn't a parseable date (e.g. already-formatted "2:14 PM"). */
function formatBubbleTime(timestamp: string): string {
  const d = new Date(timestamp);
  if (Number.isNaN(d.getTime())) return timestamp;
  return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}
