import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import styles from "./PricingTeaser.module.css";

const TIERS = [
  {
    name: "Starter",
    price: "Free",
    desc: "One voice capsule, web Mirror, and basic fidelity scoring.",
    cta: "Start free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/mo",
    desc: "Unlimited capsules, all channels, Ghostwriter queue, and priority support.",
    cta: "Get Pro",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    desc: "SSO, audit logs, custom model hosting, and dedicated onboarding.",
    cta: "Contact sales",
    highlighted: false,
  },
];

export function PricingTeaser() {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Simple pricing</h2>
        <p className={styles.lead}>Start free. Scale when your voice starts working for you.</p>
      </div>
      <div className={styles.grid}>
        {TIERS.map((t) => (
          <Card
            key={t.name}
            className={`${styles.card} ${t.highlighted ? styles.highlighted : ""}`}
          >
            <h3 className={styles.name}>{t.name}</h3>
            <div className={styles.priceWrap}>
              <span className={styles.price}>{t.price}</span>
              {t.period && <span className={styles.period}>{t.period}</span>}
            </div>
            <p className={styles.desc}>{t.desc}</p>
            <Link href="/capture">
              <Button variant={t.highlighted ? "primary" : "secondary"} className={styles.fullWidth}>
                {t.cta}
              </Button>
            </Link>
          </Card>
        ))}
      </div>
    </section>
  );
}
