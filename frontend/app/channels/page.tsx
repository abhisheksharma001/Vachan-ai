import Link from "next/link";
import { ChannelStatusGrid } from "@/components/vachan/ChannelStatusGrid";
import styles from "./page.module.css";

export default function ChannelsPage() {
  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <Link href="/" className={styles.wordmark}>
          Vachan<span>.</span>ai
        </Link>
        <div className={styles.navLinks}>
          <Link href="/dashboard" className={styles.navLink}>
            Dashboard
          </Link>
          <Link href="/mirror" className={styles.navLink}>
            Mirror
          </Link>
        </div>
      </nav>

      <main className={styles.main}>
        <header className={styles.pageHeader}>
          <h1 className={styles.title}>Channels</h1>
          <p className={styles.lead}>
            Connect your voice to every place your agents already live.
          </p>
        </header>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Connectors</h2>
          <ChannelStatusGrid />
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Export options</h2>
          <div className={styles.exportGrid}>
            <div className={styles.exportCard}>
              <span className="label">MCP live-mount</span>
              <p className={styles.exportBody}>
                For agents that can call Vachan tools live. Ideal for internal
                AI stacks and assistant platforms.
              </p>
              <button type="button" className={styles.exportAction}>
                Copy MCP config
              </button>
            </div>
            <div className={styles.exportCard}>
              <span className="label">Capsule Export Bundle</span>
              <p className={styles.exportBody}>
                A signed bundle for voice platforms (Vapi, Retell, LiveKit) that
                cannot keep a live connection.
              </p>
              <button type="button" className={styles.exportAction}>
                Download bundle
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
