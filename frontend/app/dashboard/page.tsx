import Link from "next/link";
import { DashboardGrid } from "@/components/vachan/DashboardGrid";
import { FidelityRingMini } from "@/components/vachan/FidelityRingMini";
import { RecentChats } from "@/components/vachan/RecentChats";
import { DriftAlerts } from "@/components/vachan/DriftAlerts";
import { PersonaList } from "@/components/vachan/PersonaList";
import { ChannelStatusGrid } from "@/components/vachan/ChannelStatusGrid";
import { QuickActions } from "@/components/vachan/QuickActions";
import styles from "./page.module.css";

export default function DashboardPage() {
  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <Link href="/" className={styles.wordmark}>
          Vachan<span>.</span>ai
        </Link>
        <div className={styles.navLinks}>
          <Link href="/mirror" className={styles.navLink}>
            Mirror
          </Link>
          <Link href="/channels" className={styles.navLink}>
            Channels
          </Link>
          <Link href="/capture" className={styles.cta}>
            Add sample
          </Link>
        </div>
      </nav>

      <header className={styles.header}>
        <h1 className={styles.title}>Good morning, Aakash</h1>
        <p className={styles.subtitle}>Here is how your voices are doing today.</p>
      </header>

      <DashboardGrid
        hero={
          <FidelityRingMini
            persona={{
              id: "p1",
              name: "Aakash (work)",
              fidelity: 0.84,
              band: "stable",
            }}
          />
        }
        recent={<RecentChats limit={5} />}
        alert={<DriftAlerts />}
        personas={<PersonaList />}
        channels={<ChannelStatusGrid />}
        quick={<QuickActions />}
      />
    </div>
  );
}
