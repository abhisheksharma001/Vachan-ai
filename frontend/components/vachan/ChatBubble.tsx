"use client";

import { cn } from "@/lib/utils";

type Author = "user" | "clone";

export function ChatBubble({
  author,
  children,
}: {
  author: Author;
  children: React.ReactNode;
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
            : "rounded-2xl rounded-br-none bg-sand-200 text-ink-900"
        )}
      >
        {children}
      </div>
    </div>
  );
}
