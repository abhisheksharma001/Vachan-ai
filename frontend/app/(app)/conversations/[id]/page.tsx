"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { MessageSquare, MessageSquareWarning } from "lucide-react";

import {
  useConversationMessages,
  useConversations,
} from "@/lib/api";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChatBubble } from "@/components/vachan/ChatBubble";
import { ChannelBadge } from "@/components/vachan/ChannelBadge";
import { EmptyState } from "@/components/vachan/EmptyState";
import { cn } from "@/lib/utils";

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ConversationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const messagesQuery = useConversationMessages(id);
  const conversationsQuery = useConversations();

  const conversation = conversationsQuery.data?.find(
    (c) => c.conversationId === id
  );

  const isLoading = messagesQuery.isLoading || conversationsQuery.isLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl text-ink-900">
          Conversation not found
        </h1>
        <p className="text-ink-700">
          This conversation does not exist or was removed.
        </p>
        <Link href="/conversations" className={buttonVariants()}>
          Back to conversations
        </Link>
      </div>
    );
  }

  const messages = messagesQuery.data ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink-900">
            {conversation.personaName}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <ChannelBadge channel={conversation.channel} />
            <span className="chip">
              {conversation.turnCount} turn
              {conversation.turnCount === 1 ? "" : "s"}
            </span>
            <span className="chip">Started {formatDate(conversation.startedAt)}</span>
          </div>
        </div>

        <Link
          href={`/mirror?personaId=${conversation.personaId}`}
          className={cn(buttonVariants(), "shrink-0")}
        >
          <MessageSquare className="size-4" />
          Continue in Mirror
        </Link>
      </div>

      {messagesQuery.isError ? (
        <p className="text-rose-600">
          Could not load messages: {messagesQuery.error.message}
        </p>
      ) : messages.length === 0 ? (
        <EmptyState
          icon={MessageSquareWarning}
          title="No messages"
          description="This conversation exists but has no recorded messages yet."
          action={{
            label: "Continue in Mirror",
            href: `/mirror?personaId=${conversation.personaId}`,
          }}
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
            <CardDescription>
              {messages.length} message{messages.length === 1 ? "" : "s"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {messages.map((message) => (
                <ChatBubble key={message.turnNumber} author={message.role}>
                  {message.content}
                </ChatBubble>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
