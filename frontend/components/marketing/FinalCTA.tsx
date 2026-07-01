import Link from "next/link";
import { Button } from "@/components/ui/Button";
import styles from "./FinalCTA.module.css";

export function FinalCTA() {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Every agent. Your voice.</h2>
      <p className={styles.lead}>
        Build your first Persona Capsule in under a minute. No credit card needed.
      </p>
      <Link href="/capture">
        <Button variant="primary" size="default">
          Paste your writing
        </Button>
      </Link>
    </section>
  );
}
