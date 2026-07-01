import Link from "next/link";
import styles from "./QuickActions.module.css";

export function QuickActions() {
  return (
    <div className={styles.wrap}>
      <span className="label">Quick actions</span>
      <div className={styles.grid}>
        <Link href="/capture" className={styles.action}>
          <span className={styles.icon} aria-hidden="true">＋</span>
          Add samples
        </Link>
        <Link href="/mirror" className={styles.action}>
          <span className={styles.icon} aria-hidden="true">💬</span>
          Open Mirror
        </Link>
        <Link href="/channels" className={styles.action}>
          <span className={styles.icon} aria-hidden="true">🔌</span>
          Connect channel
        </Link>
      </div>
    </div>
  );
}
