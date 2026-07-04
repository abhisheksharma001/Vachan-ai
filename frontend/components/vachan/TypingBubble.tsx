"use client";

export function TypingBubble() {
  return (
    <div className="flex w-full justify-start" role="status" aria-label="The clone is typing">
      <div className="flex max-w-[85%] items-center gap-1 rounded-2xl rounded-bl-none bg-coral-500 px-4 py-3 text-sand-50 sm:max-w-[75%]">
        <span className="size-2 animate-bounce rounded-full bg-current [animation-delay:-0.3s]" />
        <span className="size-2 animate-bounce rounded-full bg-current [animation-delay:-0.15s]" />
        <span className="size-2 animate-bounce rounded-full bg-current" />
      </div>
    </div>
  );
}
