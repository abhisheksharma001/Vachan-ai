import styles from "./PrivacyBadge.module.css";

export function PrivacyBadge({ entityCount }: { entityCount?: number }) {
  return (
    <div className={styles.wrap}>
      <span className={styles.icon} aria-hidden="true">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      </span>
      <span>
        Private details are redacted before storage.
        {entityCount != null && entityCount > 0 && (
          <span className={styles.highlight}> Found {entityCount} types in this snippet.</span>
        )}
      </span>
    </div>
  );
}
