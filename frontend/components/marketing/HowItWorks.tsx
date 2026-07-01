import styles from "./HowItWorks.module.css";

const STEPS = [
  {
    n: "01",
    title: "Paste your writing",
    body: "Notes, DMs, emails — anything you wrote. We scrub private details before storage.",
  },
  {
    n: "02",
    title: "Vachan builds your Capsule",
    body: "In under a minute you get a versioned voice identity with live fidelity scoring.",
  },
  {
    n: "03",
    title: "Mount it on any channel",
    body: "Web, WhatsApp, voice agents, or MCP live-mount. Your voice follows you everywhere.",
  },
];

export function HowItWorks() {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>How it works</h2>
      <div className={styles.grid}>
        {STEPS.map((s) => (
          <div key={s.n} className={styles.step}>
            <span className={styles.number}>{s.n}</span>
            <h3 className={styles.stepTitle}>{s.title}</h3>
            <p className={styles.body}>{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
