import styles from "./DriftAlerts.module.css";

const ALERTS: { id: string; message: string; severity: "info" | "warning" | "error" }[] = [
  { id: "1", message: "Your work clone is drifting toward generic replies.", severity: "warning" },
];

export function DriftAlerts() {
  return (
    <div className={styles.wrap}>
      <span className="label">Drift alerts</span>
      {ALERTS.length === 0 ? (
        <p className={styles.empty}>All quiet. Your clones are sounding like you.</p>
      ) : (
        <ul className={styles.list}>
          {ALERTS.map((a) => (
            <li
              key={a.id}
              className={`${styles.item} ${styles[a.severity]}`}
            >
              <span
                className={styles.dot}
                style={{ background: `var(--${a.severity === "warning" ? "amber-500" : a.severity === "error" ? "rose-600" : "teal-500"})` }}
                aria-hidden="true"
              />
              <span className={styles.message}>{a.message}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
