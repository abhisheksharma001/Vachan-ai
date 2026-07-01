import { Button } from "@/components/ui/Button";
import styles from "./GhostwriterCard.module.css";

export function GhostwriterCard({
  incoming,
  draft,
  fidelity,
  tone,
  onEdit,
  onSend,
  onReject,
}: {
  incoming: string;
  draft: string;
  fidelity?: number | null;
  tone?: string;
  onEdit: () => void;
  onSend: () => void;
  onReject?: () => void;
}) {
  return (
    <div
      className={styles.card}
      role="article"
      aria-label="Sensitive message approval"
    >
      <div className={styles.header}>
        <span className={styles.lock} aria-hidden="true">🔒</span>
        <span className={styles.title}>Sensitive — needs your approval</span>
      </div>

      <div className={styles.block}>
        <span className="label">Incoming</span>
        <p className={styles.incoming}>{incoming}</p>
      </div>

      <div className={styles.block}>
        <span className="label">Draft reply</span>
        <div className={styles.draft}>{draft}</div>
        <div className={styles.meta}>
          {fidelity != null && (
            <span className={styles.pill}>Fidelity: {Math.round(fidelity * 100)}%</span>
          )}
          {tone && <span className={styles.pill}>Tone: {tone}</span>}
        </div>
      </div>

      <div className={styles.actions}>
        <Button variant="secondary" size="sm" onClick={onEdit}>
          Edit
        </Button>
        {onReject && (
          <Button variant="ghost" size="sm" onClick={onReject}>
            Reject
          </Button>
        )}
        <Button variant="primary" size="sm" onClick={onSend}>
          Send
        </Button>
      </div>
    </div>
  );
}
