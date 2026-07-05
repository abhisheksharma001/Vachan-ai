"use client";

import { useEffect, useState } from "react";

/**
 * Screen-reader-only polite live region. Use to announce async updates
 * (chat replies, build progress, errors) without stealing focus.
 */
export function LiveRegion({ message }: { message: string }) {
  const [announced, setAnnounced] = useState("");

  useEffect(() => {
    // Small delay prevents rapid successive announcements from being swallowed.
    const t = setTimeout(() => setAnnounced(message), 150);
    return () => clearTimeout(t);
  }, [message]);

  return (
    <div aria-live="polite" aria-atomic="true" className="sr-only">
      {announced}
    </div>
  );
}
