import styles from "./ChannelCard.module.css";

export type ChannelStatus = "connected" | "setup_needed" | "error" | "unavailable";

const STATUS_STYLES: Record<
  ChannelStatus,
  { label: string; action?: string }
> = {
  connected: { label: "Live", action: "Manage" },
  setup_needed: { label: "Setup needed", action: "Continue setup" },
  error: { label: "Error", action: "Reconnect" },
  unavailable: { label: "Coming soon" },
};

export function ChannelCard({
  label,
  status,
  note,
  onAction,
}: {
  label: string;
  status: ChannelStatus;
  note?: string;
  onAction?: () => void;
}) {
  const s = STATUS_STYLES[status];
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.title}>{label}</span>
        <span className={styles.status}>
          <span className={`${styles.dot} ${styles[status]}`} aria-hidden="true" />
          {s.label}
        </span>
      </div>
      {note && <p className={styles.note}>{note}</p>}
      {s.action && status !== "unavailable" && (
        <button
          type="button"
          className={styles.action}
          onClick={onAction}
        >
          {s.action}
        </button>
      )}
    </div>
  );
}
