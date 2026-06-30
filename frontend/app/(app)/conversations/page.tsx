"use client";

import { useMemo, useState } from "react";
import { MessageSquare, Search } from "lucide-react";

import { useConversations } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationRow } from "@/components/vachan/ConversationRow";
import { EmptyState } from "@/components/vachan/EmptyState";

export default function ConversationsPage() {
  const conversationsQuery = useConversations();
  const [query, setQuery] = useState("");

  const conversations = conversationsQuery.data ?? [];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((c) =>
      c.personaName.toLowerCase().includes(q)
    );
  }, [conversations, query]);

  if (conversationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-5 w-64" />
        </div>
        <Skeleton className="h-12" />
        <div className="space-y-0">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink-900">Conversations</h1>
          <p className="mt-2 text-ink-700">Browse your past chats.</p>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-500" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by persona name..."
          className="pl-9"
        />
      </div>

      {conversations.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No conversations yet"
          description="Open the Mirror and chat with a persona to create your first conversation."
          action={{ label: "Go to Mirror", href: "/mirror" }}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No matches"
          description={`No conversations match "${query.trim()}".`}
          action={{ label: "Clear filter", onClick: () => setQuery("") }}
        />
      ) : (
        <div className="divide-y divide-sand-200 rounded-xl border border-sand-300 bg-sand-100 px-4 shadow-sm">
          {filtered.map((conversation) => (
            <ConversationRow
              key={conversation.conversationId}
              conversation={conversation}
              href={`/conversations/${conversation.conversationId}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
