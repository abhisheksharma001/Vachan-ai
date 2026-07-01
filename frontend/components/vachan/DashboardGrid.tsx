import styles from "./DashboardGrid.module.css";

export function DashboardGrid({
  hero,
  recent,
  alert,
  personas,
  channels,
  quick,
}: {
  hero: React.ReactNode;
  recent: React.ReactNode;
  alert: React.ReactNode;
  personas: React.ReactNode;
  channels: React.ReactNode;
  quick: React.ReactNode;
}) {
  return (
    <div className={styles.grid}>
      <section className={`${styles.section} ${styles.col6}`} aria-label="Primary fidelity">
        {hero}
      </section>
      <section className={`${styles.section} ${styles.col3}`} aria-label="Recent chats">
        {recent}
      </section>
      <section className={`${styles.section} ${styles.col3}`} aria-label="Drift alerts">
        {alert}
      </section>
      <section className={`${styles.section} ${styles.col4}`} aria-label="Your personas">
        {personas}
      </section>
      <section className={`${styles.section} ${styles.col3}`} aria-label="Channel status">
        {channels}
      </section>
      <section className={`${styles.section} ${styles.col5}`} aria-label="Quick actions">
        {quick}
      </section>
    </div>
  );
}
