/*
 * ChatBubble (doc 06 §6.5 #3) — the signature element of The Mirror.
 *
 *   author="clone" → coral bubble, left-aligned  (this IS "the voice")
 *   author="user"  → sand bubble, right-aligned
 *
 * TypingBubble renders the three-dot "the clone is thinking" indicator, which
 * mimics the human-pacing delay from doc 01 §1.6.
 */
import styles from "./ChatBubble.module.css";

type Author = "clone" | "user";

export function ChatBubble({
  author,
  children,
}: {
  author: Author;
  children: React.ReactNode;
}) {
  return (
    <div className={`${styles.row} ${styles[author]}`}>
      <div className={styles.bubble}>{children}</div>
    </div>
  );
}

export function TypingBubble() {
  return (
    <div className={`${styles.row} ${styles.clone}`}>
      <div
        className={styles.bubble}
        role="status"
        aria-label="The clone is typing"
      >
        <span className={styles.dots}>
          <span className={styles.dot} />
          <span className={styles.dot} />
          <span className={styles.dot} />
        </span>
      </div>
    </div>
  );
}
