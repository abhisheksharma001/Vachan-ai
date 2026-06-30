"use client";

import Link from "next/link";
import {
  BookOpen,
  Code,
  MessageSquare,
  Plus,
  User,
  Users,
} from "lucide-react";

import { useConversations, usePersonas } from "@/lib/api";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationRow } from "@/components/vachan/ConversationRow";
import { EmptyState } from "@/components/vachan/EmptyState";
import { PersonaStatusBadge } from "@/components/vachan/PersonaStatusBadge";
import type { Persona } from "@/lib/types";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-5 w-64" />
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:auto-rows-min">
        <Skeleton className="h-80 lg:col-span-7 lg:row-span-2" />
        <Skeleton className="h-48 lg:col-span-5" />
        <Skeleton className="h-48 lg:col-span-5" />
        <Skeleton className="h-32 lg:col-span-12" />
      </div>
    </div>
  );
}

function PersonaRow({ persona }: { persona: Persona }) {
  return (
    <Link
      href={`/personas/${persona.id}`}
      className="flex items-center gap-4 rounded-lg border border-sand-300 bg-sand-50 p-4 transition-colors hover:bg-sand-100"
    >
      <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-sand-200 text-ink-700">
        <User className="size-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-display text-lg font-medium text-ink-900">
            {persona.name}
          </span>
          <PersonaStatusBadge status={persona.status} />
          <span className="chip">{persona.languagePrimary}</span>
        </div>
        <p className="mt-1 text-sm text-ink-700">
          {persona.observationsCount.toLocaleString()} observation
          {persona.observationsCount === 1 ? "" : "s"}
        </p>
      </div>
      <span className="text-sm text-ink-500">
        {persona.createdAt
          ? new Date(persona.createdAt).toLocaleDateString()
          : "—"}
      </span>
    </Link>
  );
}

export default function DashboardPage() {
  const personasQuery = usePersonas();
  const conversationsQuery = useConversations();

  const personas = personasQuery.data ?? [];
  const conversations = conversationsQuery.data ?? [];
  const recentPersonas = personas.slice(0, 3);
  const recentConversations = conversations.slice(0, 5);

  const isLoading = personasQuery.isLoading || conversationsQuery.isLoading;

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (personas.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-3xl text-ink-900">Dashboard</h1>
          <p className="mt-2 text-ink-700">Welcome back to Vachan.</p>
        </div>
        <EmptyState
          icon={Users}
          title="No personas yet"
          description="Create your first persona to start capturing your voice."
          action={{ label: "Create a persona", href: "/personas" }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ink-900">Dashboard</h1>
        <p className="mt-2 text-ink-700">Welcome back to Vachan.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:auto-rows-min">
        {/* Large card: personas + create CTA */}
        <Card className="lg:col-span-7 lg:row-span-2">
          <CardHeader>
            <CardTitle>Personas</CardTitle>
            <CardDescription>Your recent voices</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentPersonas.map((persona) => (
              <PersonaRow key={persona.id} persona={persona} />
            ))}
          </CardContent>
          <CardFooter>
            <Link href="/personas" className={buttonVariants({ size: "default" })}>
              <Plus className="size-4" />
              Create a persona
            </Link>
          </CardFooter>
        </Card>

        {/* Medium card: fidelity summary */}
        <Card className="lg:col-span-5">
          <CardHeader>
            <CardTitle>Fidelity summary</CardTitle>
            <CardDescription>Average persona fidelity score</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-ink-700">
              No fidelity data yet. Chat with your personas to generate scores.
            </p>
          </CardContent>
        </Card>

        {/* Medium card: recent conversations */}
        <Card className="lg:col-span-5">
          <CardHeader>
            <CardTitle>Recent conversations</CardTitle>
            <CardDescription>
              Last {recentConversations.length} chats
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentConversations.length === 0 ? (
              <p className="py-6 text-sm text-ink-500">No conversations yet.</p>
            ) : (
              recentConversations.map((conversation) => (
                <ConversationRow
                  key={conversation.conversationId}
                  conversation={conversation}
                  href={`/conversations/${conversation.conversationId}`}
                />
              ))
            )}
          </CardContent>
        </Card>

        {/* Small card: quick links */}
        <Card className="lg:col-span-12">
          <CardHeader>
            <CardTitle>Quick links</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Link
              href="/mirror"
              className={buttonVariants({ variant: "outline" })}
            >
              <MessageSquare className="size-4" />
              Mirror
            </Link>
            <a
              href="https://github.com/abhisheksharma/Vachan.ai"
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ variant: "outline" })}
            >
              <Code className="size-4" />
              GitHub
            </a>
            <a
              href="https://github.com/abhisheksharma/Vachan.ai/tree/main/docs"
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ variant: "outline" })}
            >
              <BookOpen className="size-4" />
              Docs
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
