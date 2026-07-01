import { Card } from "@/components/ui/Card";
import styles from "./Testimonials.module.css";

const QUOTES = [
  {
    quote: "Our WhatsApp bot finally sounds like me. Customers stopped asking if it's AI.",
    name: "Aakash Sharma",
    role: "Founder, Vachan.ai",
  },
  {
    quote: "Setup took five minutes. The Hinglish replies are spot on.",
    name: "Priya Menon",
    role: "CX Lead, D2C Brand",
  },
  {
    quote: "I can hear my own voice in the email drafts. That's the trust layer we needed.",
    name: "Rahul Nair",
    role: "Sales Director",
  },
];

export function Testimonials() {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>
        What early users say
      </h2>
      <div className={styles.grid}>
        {QUOTES.map((q) => (
          <Card key={q.name}>
            <p className={styles.quote}>“{q.quote}”</p>
            <div className={styles.author}>
              <span className={styles.name}>{q.name}</span>
              <span className={styles.role}>{q.role}</span>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}
