"use client";

import Link from "next/link";
import { formatPercent } from "@/lib/utils";
import styles from "./FidelityRingMini.module.css";

export function FidelityRingMini({
  persona,
}: {
  persona?: {
    id: string;
    name: string;
    fidelity: number | null;
    band: string;
  } | null;
}) {
  if (!persona) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyTitle}>No personas yet</p>
        <p className={styles.emptyText}>
          Paste a few messages to build your first voice capsule.
        </p>
        <Link href="/capture" className={styles.emptyLink}>
          Build a voice
        </Link>
      </div>
    );
  }

  const pct = Math.round((persona.fidelity ?? 0) * 100);

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <span className="label">Voice fidelity</span>
        <span className="chip">{persona.band}</span>
      </div>
      <div className={styles.body}>
        <div
          className={styles.ring}
          style={{ ["--pct" as string]: `${pct}%` }}
        >
          <div className={styles.inner} />
          <span className={styles.score}>
            {formatPercent(persona.fidelity)}
          </span>
        </div>
        <div className={styles.info}>
          <p className={styles.name}>{persona.name}</p>
          <p className={styles.hint}>
            {pct >= 80
              ? "Your clone is sounding like you."
              : "Add more samples to push fidelity higher."}
          </p>
          <Link href={`/personas/${persona.id}`} className={styles.link}>
            View capsule →
          </Link>
        </div>
      </div>
    </div>
  );
}
