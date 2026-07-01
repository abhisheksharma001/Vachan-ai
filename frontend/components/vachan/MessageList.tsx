"use client";

import { useEffect, useRef } from "react";
import { ChatBubble, TypingBubble } from "./ChatBubble";
import type { Message } from "./ChatBubble";
import styles from "./MessageList.module.css";

export type { Message };

export function MessageList({
  messages,
  isTyping,
  children,
}: {
  messages: Message[];
  isTyping?: boolean;
  children?: React.ReactNode;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isTyping]);

  return (
    <div
      className={styles.scroll}
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-relevant="additions"
    >
      {messages.map((m, i) => (
        <ChatBubble key={i} author={m.role} timestamp={m.timestamp}>
          {m.content}
        </ChatBubble>
      ))}
      {isTyping && <TypingBubble />}
      {children}
      <div ref={endRef} />
    </div>
  );
}
