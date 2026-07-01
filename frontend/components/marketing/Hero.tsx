import Link from "next/link";
import { Button } from "@/components/ui/Button";
import styles from "./Hero.module.css";

export function Hero() {
  return (
    <section className={styles.section}>
      <div className={styles.content}>
        <p className={styles.eyebrow}>
          Sound like you — everywhere
        </p>
        <h1 className={styles.title}>Every agent. Your voice.</h1>
        <p className={styles.lead}>
          Vachan learns how <em className={styles.emphasis}>you</em> actually talk — your
          warmth, your pacing, your Hinglish — so every reply your agents send still sounds
          like you wrote it.
        </p>
        <div className={styles.actions}>
          <Link href="/capture">
            <Button variant="primary">Paste your writing</Button>
          </Link>
          <Link href="#mirror-preview">
            <Button variant="secondary">See how it works</Button>
          </Link>
        </div>
        <p className={styles.trust}>
          Private details are redacted before storage.
        </p>
      </div>
      <div className={styles.preview} aria-label="Mirror chat preview">
        <div className={styles.phone}>
          <div className={`${styles.bubble} ${styles.user}`}>
            hey can you reply to clients for me?
          </div>
          <div className={`${styles.bubble} ${styles.clone}`}>
            haan bilkul! main aapke tone mein reply karunga 🙌
          </div>
          <div className={`${styles.bubble} ${styles.user}`}>
            cool. tell them to call me at +91 98765 43210
          </div>
          <div className={`${styles.bubble} ${styles.clone}`}>
            got it — I&apos;ll share <span className={styles.pii}>[IN_PHONE]</span> with them.
          </div>
        </div>
      </div>
    </section>
  );
}
