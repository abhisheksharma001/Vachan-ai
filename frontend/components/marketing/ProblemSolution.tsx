import { Card } from "@/components/ui/Card";
import styles from "./ProblemSolution.module.css";

export function ProblemSolution() {
  return (
    <section className={styles.section}>
      <div className={styles.intro}>
        <h2 className={styles.title}>Your agents sound like robots.</h2>
        <p className={styles.lead}>
          Customers can tell. Colleagues can tell. You can tell. Generic AI replies
          erode trust one interaction at a time.
        </p>
      </div>
      <div className={styles.grid}>
        <Card>
          <h3 className={styles.cardTitle}>Capture your voice</h3>
          <p className={styles.cardBody}>
            Paste messages, upload a WhatsApp export, or answer a few questions.
            Vachan extracts warmth, pacing, formality, and Hinglish mix.
          </p>
        </Card>
        <Card>
          <h3 className={styles.cardTitle}>Build a Capsule</h3>
          <p className={styles.cardBody}>
            A versioned, portable voice identity — not a prompt hack. Govern it,
            roll it back, and mount it anywhere.
          </p>
        </Card>
        <Card>
          <h3 className={styles.cardTitle}>Deploy everywhere</h3>
          <p className={styles.cardBody}>
            Web chat, WhatsApp, Telegram, voice agents, or any MCP-compatible
            agent. Same voice, every channel.
          </p>
        </Card>
      </div>
    </section>
  );
}
