import Link from "next/link";
import styles from "./PersonaList.module.css";

const PERSONAS = [
  { id: "p1", name: "Aakash (work)", band: "stable", fidelity: 0.84 },
  { id: "p2", name: "Aakash (WhatsApp)", band: "calibrating", fidelity: 0.72 },
];

const BAND_CHIP = {
  stable: styles.bandStable,
  calibrating: styles.bandCalibrating,
  warming_up: styles.bandWarming,
};

export function PersonaList() {
  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <span className="label">Your personas</span>
        <Link href="/capture" className={styles.addLink}>
          Add new →
        </Link>
      </div>
      <ul className={styles.list}>
        {PERSONAS.map((p) => (
          <li key={p.id}>
            <Link
              href={`/personas/${p.id}`}
              className={styles.itemLink}
            >
              <span className={styles.name}>{p.name}</span>
              <span className={`chip ${styles.band} ${BAND_CHIP[p.band as keyof typeof BAND_CHIP] || ""}`}>{p.band}</span>
              <span className={styles.fidelity}>
                {Math.round(p.fidelity * 100)}%
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
