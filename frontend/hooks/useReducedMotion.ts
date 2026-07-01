"use client";

import { useEffect, useState } from "react";

/**
 * Detect the user's motion preference. Use this to disable non-essential
 * animations for users with vestibular disorders or who prefer reduced motion.
 */
export function useReducedMotion(): boolean {
  const [reduce, setReduce] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduce(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduce(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return reduce;
}
