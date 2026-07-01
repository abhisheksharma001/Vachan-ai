import Link from "next/link";
import { ChatBubble, TypingBubble } from "@/components/vachan/ChatBubble";
import { Button } from "@/components/ui/Button";
import styles from "./MirrorPreview.module.css";

export function MirrorPreview() {
  return (
    <section className={styles.section} id="mirror-preview">
      <div className={styles.intro}>
        <h2 className={styles.title}>A peek at the Mirror</h2>
        <p className={styles.lead}>
          Chat with your clone, tune tone on the fly, and watch every reply score
          itself for fidelity.
        </p>
      </div>
      <div className={styles.grid}>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div className={styles.avatar} aria-hidden="true" />
            <span className={styles.panelTitle}>Your clone</span>
            <span className={`chip ${styles.status}`}>warming up</span>
          </div>
          <div className={styles.panelBody}>
            <ChatBubble author="user">hey can you reply to clients for me?</ChatBubble>
            <ChatBubble author="clone">haan bilkul! main aapke tone mein reply karunga 🙌</ChatBubble>
            <ChatBubble author="user">cool. tell them to call me at +91 98765 43210</ChatBubble>
            <ChatBubble author="clone">
              got it — I&apos;ll share <span className={styles.pii}>[IN_PHONE]</span> with them.
            </ChatBubble>
            <TypingBubble />
          </div>
        </div>
        <div className={styles.ctaCol}>
          <Link href="/mirror">
            <Button variant="primary">Try the real Mirror</Button>
          </Link>
          <p className={styles.hint}>No signup required for the demo.</p>
        </div>
      </div>
    </section>
  );
}
