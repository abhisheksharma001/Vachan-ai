import { ChannelCard, type ChannelStatus } from "./ChannelCard";
import styles from "./ChannelStatusGrid.module.css";

const CHANNELS: { id: string; label: string; status: ChannelStatus; note?: string }[] = [
  { id: "web", label: "Web / Mirror", status: "connected", note: "Primary sandbox — ready to chat." },
  { id: "whatsapp", label: "WhatsApp", status: "setup_needed", note: "Requires Meta Cloud API + business verification." },
  { id: "telegram", label: "Telegram", status: "setup_needed", note: "Bot API workspace install." },
  { id: "voice", label: "Voice (Vapi/Retell)", status: "setup_needed", note: "Exports signed Capsule Bundle + voice KB." },
  { id: "mcp", label: "MCP live-mount", status: "setup_needed", note: "For agents that can call Vachan tools live." },
];

export function ChannelStatusGrid() {
  return (
    <div className={styles.grid} role="list" aria-label="Channel connectors">
      {CHANNELS.map((c) => (
        <div key={c.id} role="listitem">
          <ChannelCard label={c.label} status={c.status} note={c.note} />
        </div>
      ))}
    </div>
  );
}
