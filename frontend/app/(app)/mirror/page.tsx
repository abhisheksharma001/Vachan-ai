"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import {
  useRouter,
  useSearchParams,
} from "next/navigation";
import {
  FileDown,
  Loader2,
  MessageSquare,
  Pencil,
  Send,
  Users,
} from "lucide-react";

import {
  type ChatTurn,
  useChatWithClone,
  usePersona,
  usePersonas,
  useVoiceKb,
} from "@/lib/api";
import type { Channel, Fidelity, Tone } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ChatBubble } from "@/components/vachan/ChatBubble";
import { EmptyState } from "@/components/vachan/EmptyState";
import { FidelityRing } from "@/components/vachan/FidelityRing";
import { PersonaStatusBadge } from "@/components/vachan/PersonaStatusBadge";
import { TonalitySliders } from "@/components/vachan/TonalitySliders";
import { TypingBubble } from "@/components/vachan/TypingBubble";

const CHANNELS: { value: Channel; label: string }[] = [
  { value: "chat", label: "Chat" },
  { value: "english", label: "English" },
  { value: "email", label: "Email" },
  { value: "voice", label: "Voice" },
];

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function typingDelayMs(text: string): number {
  const reduce =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return 0;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  return Math.min(words * 45, 2200);
}

export default function MirrorPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <Skeleton className="h-10 w-56" />
          <Skeleton className="h-96" />
        </div>
      }
    >
      <MirrorPageContent />
    </Suspense>
  );
}

function MirrorPageContent() {
  const searchParams = useSearchParams();
  const personaId = searchParams.get("personaId") ?? undefined;

  if (!personaId) {
    return <PersonaPicker />;
  }

  return <MirrorChat personaId={personaId} />;
}

function PersonaPicker() {
  const router = useRouter();
  const personasQuery = usePersonas();
  const [selectedId, setSelectedId] = useState("");

  const personas = personasQuery.data ?? [];

  if (personasQuery.isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-10 w-48" />
          <Skeleton className="mt-2 h-5 w-64" />
        </div>
        <Skeleton className="h-40" />
      </div>
    );
  }

  if (personas.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-3xl text-ink-900">The Mirror</h1>
          <p className="mt-2 text-ink-700">Chat with your clone.</p>
        </div>
        <EmptyState
          icon={Users}
          title="No personas yet"
          description="Create a persona before you can open the Mirror."
          action={{ label: "Create a persona", href: "/personas" }}
        />
      </div>
    );
  }

  const start = () => {
    if (!selectedId) return;
    router.replace(`/mirror?personaId=${selectedId}`);
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="text-center">
        <h1 className="font-display text-3xl text-ink-900">The Mirror</h1>
        <p className="mt-2 text-ink-700">Choose a persona to start chatting.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Start a chat</CardTitle>
          <CardDescription>
            Pick one of your existing personas to mirror.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <label htmlFor="persona-select" className="label">
              Persona
            </label>
            <select
              id="persona-select"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="h-10 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-base outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm"
            >
              <option value="" disabled>
                Select a persona
              </option>
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <Button
            onClick={start}
            disabled={!selectedId}
            className="w-full"
          >
            <MessageSquare className="size-4" />
            Start chat
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function MirrorChat({ personaId }: { personaId: string }) {
  const personaQuery = usePersona(personaId);
  const voiceKb = useVoiceKb();

  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [channel, setChannel] = useState<Channel>("chat");
  const [tone, setTone] = useState<Tone>({
    warmth: 0.5,
    directness: 0.5,
    formality: 0.5,
    hinglish: 0.5,
  });
  const [lastFidelity, setLastFidelity] = useState<Fidelity | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [isCorrectionMode, setIsCorrectionMode] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setLastFidelity(null);
    setDraft("");
    setIsTyping(false);
    setIsCorrectionMode(false);
  }, [personaId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const chat = useChatWithClone({
    onSuccess: (data) => {
      // Corrections receive an empty reply and should not add a clone turn.
      if (!data.reply) {
        setIsTyping(false);
        return;
      }
      const delay = typingDelayMs(data.reply);
      window.setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          { role: "clone", content: data.reply },
        ]);
        setLastFidelity(data.fidelity ?? null);
        setIsTyping(false);
      }, delay);
    },
    onError: () => {
      setIsTyping(false);
    },
  });

  const send = () => {
    const text = draft.trim();
    if (!text || isTyping || chat.isPending) return;

    const history = messages;
    const isCorrection = isCorrectionMode;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text, isCorrection },
    ]);
    setDraft("");

    chat.mutate({
      personaId,
      message: text,
      history,
      channel,
      tone,
      isCorrection,
    });

    if (isCorrection) {
      // One-shot toggle: avoid accidentally sending every follow-up as a correction.
      setIsCorrectionMode(false);
    } else {
      setIsTyping(true);
    }
  };

  const exportVoiceKb = () => {
    voiceKb.mutate(personaId, {
      onSuccess: (data) => {
        downloadJson(`voice-kb-${personaId}.json`, data);
      },
    });
  };

  const persona = personaQuery.data;

  if (personaQuery.isLoading) {
    return (
      <div className="flex h-full min-h-0 flex-col gap-4">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="flex-1" />
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl text-ink-900">Persona not found</h1>
        <p className="text-ink-700">
          The selected persona does not exist or was deleted.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display text-3xl text-ink-900">
              {persona.name}
            </h1>
            <PersonaStatusBadge status={persona.status} />
          </div>
          <p className="mt-1 text-ink-700">
            Chat with your clone in the tone of this persona.
          </p>
        </div>

        <Tabs
          value={channel}
          onValueChange={(value) => value && setChannel(value as Channel)}
        >
          <TabsList>
            {CHANNELS.map((c) => (
              <TabsTrigger key={c.value} value={c.value}>
                {c.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* Chat + sidebar */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="flex min-h-0 flex-col lg:col-span-2">
          <CardContent className="flex min-h-0 flex-1 flex-col gap-4 pt-4">
            <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto rounded-xl border border-sand-300 bg-sand-50 p-4">
              {messages.length === 0 && (
                <p className="m-auto text-sm text-ink-500">
                  Type a message to start the conversation.
                </p>
              )}
              {messages.map((turn, idx) => (
                <ChatBubble
                  key={idx}
                  author={turn.role}
                  isCorrection={turn.isCorrection}
                >
                  {turn.content}
                </ChatBubble>
              ))}
              {isTyping && <TypingBubble />}
              <div ref={scrollRef} />
            </div>

            {chat.isError && (
              <p className="text-sm text-rose-600">{chat.error.message}</p>
            )}

            <div className="flex items-start gap-2">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={
                  isCorrectionMode
                    ? "Correction: this will not get a reply..."
                    : "Say something..."
                }
                rows={1}
                disabled={isTyping || chat.isPending}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                className="min-h-10 flex-1 resize-none"
              />
              <Button
                type="button"
                variant={isCorrectionMode ? "default" : "outline"}
                aria-pressed={isCorrectionMode}
                onClick={() => setIsCorrectionMode((v) => !v)}
                disabled={chat.isPending}
                className="shrink-0"
                title="Toggle correction mode"
              >
                <Pencil className="size-4" />
                <span className="hidden sm:inline">Correction</span>
              </Button>
              <Button
                onClick={send}
                disabled={isTyping || chat.isPending || !draft.trim()}
                className="shrink-0"
              >
                {chat.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Send className="size-4" />
                )}
                Send
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6 lg:col-span-1">
          <FidelityRing fidelity={lastFidelity} band={persona.status} />
          <TonalitySliders
            tone={tone}
            onChange={setTone}
            disabled={isTyping || chat.isPending}
          />
          <Button
            variant="outline"
            className="w-full"
            onClick={exportVoiceKb}
            disabled={voiceKb.isPending}
          >
            {voiceKb.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <FileDown className="size-4" />
            )}
            Export voice KB
          </Button>
        </div>
      </div>
    </div>
  );
}
