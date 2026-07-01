import Link from "next/link";
import { Button } from "@/components/ui/Button";
import styles from "./PersonaHeader.module.css";

const BAND_CHIP = {
  stable: styles.bandStable,
  calibrating: styles.bandCalibrating,
  warming_up: styles.bandWarming,
};

export function PersonaHeader({
  personaId,
  name = "Aakash (work)",
  band = "stable",
  confidence = 0.84,
  evidenceTokens = 14200,
}: {
  personaId: string;
  name?: string;
  band?: string;
  confidence?: number;
  evidenceTokens?: number;
}) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link href="/dashboard" className={styles.back}>
          ← Back to dashboard
        </Link>
        <div className={styles.identity}>
          <div className={styles.avatar} aria-hidden="true">
            {initials}
          </div>
          <div className={styles.identityText}>
            <h1 className={styles.title}>{name}</h1>
            <div className={styles.meta}>
              <span
                className={`chip ${styles.band} ${
                  BAND_CHIP[band as keyof typeof BAND_CHIP] || ""
                }`}
              >
                {band}
              </span>
              <span className={styles.id}>ID: {personaId}</span>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.right}>
        <div className={styles.stats}>
          <div className={styles.stat}>
            <span className={styles.statValue}>{Math.round(confidence * 100)}%</span>
            <span className={styles.statLabel}>Confidence</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statValue}>{evidenceTokens.toLocaleString()}</span>
            <span className={styles.statLabel}>Evidence tokens</span>
          </div>
        </div>
        <div className={styles.actions}>
          <Link href={`/mirror?personaId=${personaId}`}>
            <Button variant="secondary" size="sm">
              Test in Mirror
            </Button>
          </Link>
          <Button variant="primary" size="sm">
            Export
          </Button>
        </div>
      </div>
    </header>
  );
}
