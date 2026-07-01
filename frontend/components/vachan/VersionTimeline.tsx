"use client";

import { Button } from "@/components/ui/Button";
import styles from "./VersionTimeline.module.css";

const VERSIONS = [
  {
    id: "v12",
    number: 12,
    current: true,
    date: "now",
    band: "stable",
    diff: "Hinglish 29% → 33%, formality 0.45 → 0.40",
  },
  {
    id: "v11",
    number: 11,
    current: false,
    date: "2d ago",
    band: "calibrating",
    diff: "Added WhatsApp samples",
  },
  {
    id: "v10",
    number: 10,
    current: false,
    date: "5d ago",
    band: "warming_up",
    diff: "Manual baseline",
  },
];

const BAND_CHIP = {
  stable: styles.bandStable,
  calibrating: styles.bandCalibrating,
  warming_up: styles.bandWarming,
};

export function VersionTimeline({ personaId }: { personaId: string }) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHead}>
        <div>
          <span className="label">Version history</span>
          <p className={styles.sub}>Every change to this capsule, newest first.</p>
        </div>
      </div>
      <ul className={styles.list} aria-label={`Version history for persona ${personaId}`}>
        {VERSIONS.map((v, idx) => (
          <li key={v.id} className={styles.item}>
            <div className={styles.lineColumn}>
              <span
                className={`${styles.marker} ${v.current ? styles.current : ""}`}
                aria-hidden="true"
              />
              {idx !== VERSIONS.length - 1 && <span className={styles.line} aria-hidden="true" />}
            </div>
            <div className={styles.body}>
              <div className={styles.head}>
                <span className={styles.version}>v{v.number}</span>
                <span className={styles.date}>{v.date}</span>
                <span
                  className={`chip ${styles.band} ${
                    BAND_CHIP[v.band as keyof typeof BAND_CHIP] || ""
                  }`}
                >
                  {v.band}
                </span>
              </div>
              <p className={styles.diff}>{v.diff}</p>
            </div>
            {!v.current && (
              <Button variant="ghost" size="sm">
                Rollback
              </Button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
