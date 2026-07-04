"use client";

import Link from "next/link";
import { MessageCircle } from "lucide-react";
import { ChannelBadge } from "./ChannelBadge";
import type { Conversation } from "@/lib/types";
import { cn } from "@/lib/utils";

function relativeTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

export function ConversationRow({
  conversation,
  href,
  className,
}: {
  conversation: Conversation;
  href: string;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center justify-between gap-4 border-b border-sand-200 py-4 transition-colors hover:bg-sand-100/60",
        className
      )}
    >
      <div className="min-w-0">
        <p className="truncate font-medium text-ink-900">
          {conversation.personaName}
        </p>
        <p className="mt-0.5 text-sm text-ink-500">
          {relativeTime(conversation.lastActiveAt)}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <ChannelBadge channel={conversation.channel} />
        <span className="chip">
          <MessageCircle className="size-3" />
          {conversation.turnCount} turn{conversation.turnCount === 1 ? "" : "s"}
        </span>
      </div>
    </Link>
  );
}
