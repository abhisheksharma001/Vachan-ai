"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import {
  Copy,
  Edit2,
  FileDown,
  Loader2,
  Send,
  Users,
} from "lucide-react";

import {
  type ChatTurn,
  useCaptureToPersona,
  useChatWithClone,
  usePersona,
  usePersonaCapsule,
  useUpdatePersona,
  useVoiceKb,
} from "@/lib/api";
import type { Fidelity, Tone } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ChatBubble } from "@/components/vachan/ChatBubble";
import { FidelityRing } from "@/components/vachan/FidelityRing";
import { PersonaStatusBadge } from "@/components/vachan/PersonaStatusBadge";
import { TonalitySliders } from "@/components/vachan/TonalitySliders";
import { TypingBubble } from "@/components/vachan/TypingBubble";

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

export default function PersonaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const personaQuery = usePersona(id);
  const capsuleQuery = usePersonaCapsule(id);
  const updatePersona = useUpdatePersona();
  const voiceKb = useVoiceKb();

  const [renameOpen, setRenameOpen] = useState(false);
  const [renameName, setRenameName] = useState("");

  const persona = personaQuery.data;

  const startRename = () => {
    if (!persona) return;
    setRenameName(persona.name);
    setRenameOpen(true);
  };

  const submitRename = () => {
    const trimmed = renameName.trim();
    if (!trimmed || !persona) return;
    updatePersona.mutate(
      { id: persona.id, name: trimmed },
      { onSuccess: () => setRenameOpen(false) }
    );
  };

  const exportVoiceKb = () => {
    voiceKb.mutate(id, {
      onSuccess: (data) => {
        downloadJson(`voice-kb-${id}.json`, data);
      },
    });
  };

  if (personaQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl text-ink-900">Persona not found</h1>
        <p className="text-ink-700">
          The persona you are looking for does not exist or was deleted.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-display text-3xl text-ink-900">
              {persona.name}
            </h1>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={startRename}
              aria-label="Rename persona"
            >
              <Edit2 className="size-4" />
            </Button>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <PersonaStatusBadge status={persona.status} />
            <span className="chip">{persona.languagePrimary}</span>
            <span className="chip">v{persona.currentCapsuleVersion}</span>
            <span className="chip">
              {persona.createdAt
                ? new Date(persona.createdAt).toLocaleDateString()
                : "—"}
            </span>
          </div>
        </div>

        <Button
          variant="outline"
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

      <Tabs defaultValue="mirror" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="mirror">Mirror</TabsTrigger>
          <TabsTrigger value="capture">Capture</TabsTrigger>
          <TabsTrigger value="capsule">Capsule</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="mirror" className="space-y-4">
          <MirrorTab personaId={id} />
        </TabsContent>

        <TabsContent value="capture" className="space-y-4">
          <CaptureTab personaId={id} />
        </TabsContent>

        <TabsContent value="capsule" className="space-y-4">
          <CapsuleTab query={capsuleQuery} />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <HistoryTab persona={persona} />
        </TabsContent>
      </Tabs>

      {/* Rename dialog */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename persona</DialogTitle>
            <DialogDescription>Update the display name.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="rename-name" className="label">
                Name
              </label>
              <Input
                id="rename-name"
                value={renameName}
                onChange={(e) => setRenameName(e.target.value)}
                disabled={updatePersona.isPending}
              />
            </div>
          </div>
          {updatePersona.isError && (
            <p className="mb-4 text-sm text-rose-600">
              {updatePersona.error.message}
            </p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRenameOpen(false)}
              disabled={updatePersona.isPending}
            >
              Cancel
            </Button>
            <Button onClick={submitRename} disabled={updatePersona.isPending}>
              {updatePersona.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function MirrorTab({ personaId }: { personaId: string }) {
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [lastFidelity, setLastFidelity] = useState<Fidelity | null>(null);
  const [tone, setTone] = useState<Tone>({
    warmth: 0.5,
    directness: 0.5,
    formality: 0.5,
    hinglish: 0.5,
  });

  const chat = useChatWithClone({
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: draft.trim() },
        { role: "clone", content: data.reply },
      ]);
      setDraft("");
      setLastFidelity(data.fidelity ?? null);
    },
  });

  const send = () => {
    const text = draft.trim();
    if (!text || chat.isPending) return;
    chat.mutate({
      personaId,
      message: text,
      history: messages,
      channel: "chat",
      tone,
    });
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Chat with this persona</CardTitle>
          <CardDescription>
            Try a compact mirror conversation here.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex max-h-[420px] min-h-[240px] flex-col gap-3 overflow-y-auto rounded-xl border border-sand-300 bg-sand-50 p-4">
            {messages.length === 0 && (
              <p className="m-auto text-sm text-ink-500">
                Type a message to start the conversation.
              </p>
            )}
            {messages.map((turn, idx) => (
              <ChatBubble key={idx} author={turn.role}>
                {turn.content}
              </ChatBubble>
            ))}
            {chat.isPending && <TypingBubble />}
          </div>
          {chat.isError && (
            <p className="text-sm text-rose-600">{chat.error.message}</p>
          )}
          <div className="flex gap-2">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Say something..."
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              disabled={chat.isPending}
              className="flex-1"
            />
            <Button onClick={send} disabled={chat.isPending || !draft.trim()}>
              <Send className="size-4" />
              Send
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <FidelityRing fidelity={lastFidelity} />
        <TonalitySliders tone={tone} onChange={setTone} />
      </div>
    </div>
  );
}

function CaptureTab({ personaId }: { personaId: string }) {
  const [text, setText] = useState("");
  const capture = useCaptureToPersona();

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || capture.isPending) return;
    capture.mutate({ personaId, text: trimmed });
  };

  const style = capture.data?.style;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Capture writing</CardTitle>
          <CardDescription>
            Paste messages, emails, or notes that sound like this persona.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste a paragraph or two of real writing..."
            rows={10}
            disabled={capture.isPending}
          />
          {capture.isError && (
            <p className="text-sm text-rose-600">{capture.error.message}</p>
          )}
          <Button
            onClick={submit}
            disabled={capture.isPending || text.trim().length < 20}
          >
            {capture.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : null}
            Capture to persona
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Capture summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!capture.data ? (
            <p className="text-sm text-ink-500">
              Submit writing to see token and style summary.
            </p>
          ) : (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-ink-700">Band</span>
                <span className="font-medium text-ink-900">
                  {capture.data.band ?? "—"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-ink-700">Stored</span>
                <span className="font-medium text-ink-900">
                  {capture.data.stored ?? "—"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-ink-700">Total tokens</span>
                <span className="font-medium text-ink-900">
                  {capture.data.totalTokens?.toLocaleString() ?? "—"}
                </span>
              </div>
              {style && Object.keys(style).length > 0 && (
                <pre className="max-h-60 overflow-auto rounded-lg border border-sand-300 bg-sand-50 p-3 text-xs">
                  {JSON.stringify(style, null, 2)}
                </pre>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CapsuleTab({
  query,
}: {
  query: ReturnType<typeof usePersonaCapsule>;
}) {
  const [copied, setCopied] = useState(false);

  const raw = query.data ?? {};
  const text = JSON.stringify(raw, null, 2);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (query.isLoading) {
    return <Skeleton className="h-96" />;
  }

  if (query.isError) {
    return (
      <p className="text-rose-600">
        Could not load capsule: {query.error.message}
      </p>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>Persona capsule</CardTitle>
          <CardDescription>Read-only view of the current capsule.</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={copy}>
          <Copy className="size-4" />
          {copied ? "Copied" : "Copy"}
        </Button>
      </CardHeader>
      <CardContent>
        <Textarea
          readOnly
          value={text}
          className="min-h-[400px] font-mono text-xs"
        />
      </CardContent>
    </Card>
  );
}

function HistoryTab({ persona }: { persona: { currentCapsuleVersion: number } }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Version history</CardTitle>
        <CardDescription>Capsule timeline and edits.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3 rounded-lg border border-sand-300 bg-sand-50 p-3">
          <Users className="size-4 text-coral-500" />
          <div>
            <p className="text-sm font-medium text-ink-900">
              Current capsule v{persona.currentCapsuleVersion}
            </p>
            <p className="text-xs text-ink-500">Latest active version</p>
          </div>
        </div>
        <p className="text-sm text-ink-700">
          Full version timeline coming soon.
        </p>
      </CardContent>
    </Card>
  );
}
