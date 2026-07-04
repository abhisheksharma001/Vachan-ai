"use client";

import { Mail, MessageSquare, Mic, type LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Channel } from "@/lib/types";

const ICONS: Record<Channel, LucideIcon> = {
  chat: MessageSquare,
  english: MessageSquare,
  email: Mail,
  voice: Mic,
};

const LABELS: Record<Channel, string> = {
  chat: "Chat",
  english: "English",
  email: "Email",
  voice: "Voice",
};

export function ChannelBadge({ channel }: { channel: string }) {
  const key = (channel as Channel) in ICONS ? (channel as Channel) : "chat";
  const Icon = ICONS[key];
  return (
    <Badge variant="secondary" className="gap-1 capitalize">
      <Icon className="size-3" />
      {LABELS[key]}
    </Badge>
  );
}
