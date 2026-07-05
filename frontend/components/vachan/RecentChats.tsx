import Link from "next/link";
import styles from "./RecentChats.module.css";

const PLACEHOLDER = [
  { id: "1", title: "Client follow-up", preview: "haan bilkul, kal tak bhej deta hu", time: "2h ago" },
  { id: "2", title: "Vendor negotiation", preview: "price thoda aur negotiable hai?", time: "1d ago" },
];

export function RecentChats({ limit = 5 }: { limit?: number }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <span className="label">Recent chats</span>
        <Link href="/mirror" className={styles.openLink}>
          Open Mirror →
        </Link>
      </div>
      <ul className={styles.list}>
        {PLACEHOLDER.slice(0, limit).map((chat) => (
          <li key={chat.id} className={styles.item}>
            <Link href={`/mirror?chat=${chat.id}`} className={styles.link}>
              <span className={styles.title}>{chat.title}</span>
              <span className={styles.preview}>{chat.preview}</span>
              <span className={styles.time}>{chat.time}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
