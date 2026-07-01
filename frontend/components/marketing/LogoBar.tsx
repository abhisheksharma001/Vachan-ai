import styles from "./LogoBar.module.css";

const LOGOS = ["Linear", "Notion", "Figma", "Stripe", "Vercel"];

export function LogoBar() {
  return (
    <section className={styles.section}>
      <p className={styles.lead}>
        Trusted by teams that care about voice
      </p>
      <div className={styles.logos}>
        {LOGOS.map((name) => (
          <span key={name} className={styles.logo} aria-label={name}>
            {name}
          </span>
        ))}
      </div>
    </section>
  );
}
