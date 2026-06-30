"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";

import type {
  Channel,
  Conversation,
  Fidelity,
  Message,
  Persona,
  Role,
  Tone,
} from "./types";

/* -------------------------------------------------------------------------- */
/* Query keys                                                                 */
/* -------------------------------------------------------------------------- */

export const keys = {
  personas: ["personas"] as const,
  persona: (id: string) => ["personas", id] as const,
  conversations: ["conversations"] as const,
  messages: (id: string) => ["conversations", id, "messages"] as const,
};

/* -------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* -------------------------------------------------------------------------- */

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Request failed (${res.status})`);
  }
  return res.json();
}

function undefToNull<T>(v: T | undefined): T | null {
  return v === undefined ? null : v;
}

function toPersona(raw: Record<string, unknown>): Persona {
  return {
    id: String(raw.persona_id ?? raw.id ?? ""),
    name: String(raw.name ?? ""),
    status: String(raw.status ?? "warming_up"),
    languagePrimary: String(raw.language_primary ?? raw.languagePrimary ?? ""),
    currentCapsuleVersion: Number(raw.current_capsule_version ?? raw.currentCapsuleVersion ?? 0),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ""),
    observationsCount: Number(raw.observations_count ?? raw.observationsCount ?? 0),
  };
}

function toConversation(raw: Record<string, unknown>): Conversation {
  return {
    conversationId: String(raw.conversation_id ?? raw.conversationId ?? ""),
    personaId: String(raw.persona_id ?? raw.personaId ?? ""),
    personaName: String(raw.persona_name ?? raw.personaName ?? ""),
    channel: String(raw.channel ?? "chat") as Channel,
    capsuleVersion: Number(raw.capsule_version ?? raw.capsuleVersion ?? 0),
    startedAt: String(raw.started_at ?? raw.startedAt ?? ""),
    lastActiveAt: String(raw.last_active_at ?? raw.lastActiveAt ?? ""),
    turnCount: Number(raw.turn_count ?? raw.turnCount ?? 0),
  };
}

function toMessage(raw: Record<string, unknown>): Message {
  return {
    turnNumber: Number(raw.turn_number ?? raw.turnNumber ?? 0),
    role: String(raw.role ?? "user") as Role,
    content: String(raw.content ?? ""),
    pfsScore: undefToNull(raw.pfs_score ?? raw.pfsScore) as number | null,
    modelUsed: String(raw.model_used ?? raw.modelUsed ?? ""),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ""),
  };
}

/* -------------------------------------------------------------------------- */
/* Fetch functions                                                            */
/* -------------------------------------------------------------------------- */

export async function fetchPersonas(): Promise<Persona[]> {
  const data = await fetchJson<Record<string, unknown> | unknown[]>("/api/personas");
  const list = Array.isArray(data) ? data : (data.personas as unknown[]) ?? [];
  return list.map((p) => toPersona(p as Record<string, unknown>));
}

export async function fetchPersona(id: string): Promise<Persona> {
  const data = await fetchJson<Record<string, unknown>>(`/api/personas/${id}`);
  return toPersona(data);
}

export async function createPersona(body: {
  name: string;
  languagePrimary?: string;
}): Promise<Persona> {
  const data = await fetchJson<Record<string, unknown>>("/api/personas", {
    method: "POST",
    body: JSON.stringify({
      name: body.name,
      language_primary: body.languagePrimary,
    }),
  });
  return toPersona(data);
}

export async function updatePersona(
  id: string,
  body: { name?: string; languagePrimary?: string },
): Promise<Persona> {
  const data = await fetchJson<Record<string, unknown>>(`/api/personas/${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: body.name,
      language_primary: body.languagePrimary,
    }),
  });
  return toPersona(data);
}

export async function deletePersona(id: string): Promise<void> {
  await fetchJson<Record<string, unknown>>(`/api/personas/${id}`, {
    method: "DELETE",
  });
}

export async function fetchConversations(): Promise<Conversation[]> {
  const data = await fetchJson<Record<string, unknown> | unknown[]>("/api/conversations");
  const list = Array.isArray(data) ? data : (data.conversations as unknown[]) ?? [];
  return list.map((c) => toConversation(c as Record<string, unknown>));
}

export async function fetchConversationMessages(id: string): Promise<Message[]> {
  const data = await fetchJson<Record<string, unknown> | unknown[]>(
    `/api/conversations/${id}/messages`,
  );
  const list = Array.isArray(data) ? data : (data.messages as unknown[]) ?? [];
  return list.map((m) => toMessage(m as Record<string, unknown>));
}

export async function createConversation(body: {
  personaId: string;
  channel?: Channel;
}): Promise<Conversation> {
  const data = await fetchJson<Record<string, unknown>>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({
      personaId: body.personaId,
      channel: body.channel ?? "chat",
    }),
  });
  return toConversation(data);
}

export type CaptureMirrorResult = {
  personaId: string;
  band?: string;
  stored?: number;
  totalTokens?: number;
  style?: Record<string, unknown>;
  capsuleData?: Record<string, unknown> | null;
};

export async function captureWriting(
  text: string,
  sourceType = "paste",
): Promise<CaptureMirrorResult> {
  return fetchJson<CaptureMirrorResult>("/api/mirror/capture", {
    method: "POST",
    body: JSON.stringify({ text, sourceType }),
  });
}

export type CaptureToPersonaResult = {
  band?: string;
  stored?: number;
  totalTokens?: number;
  style?: Record<string, unknown>;
};

export async function captureToPersona(
  personaId: string,
  text: string,
  sourceType = "paste",
): Promise<CaptureToPersonaResult> {
  return fetchJson<CaptureToPersonaResult>(`/api/personas/${personaId}/capture`, {
    method: "POST",
    body: JSON.stringify({ text, sourceType }),
  });
}

export type ChatTurn = { role: Role; content: string };

export type ChatWithCloneResult = {
  reply: string;
  fidelity?: Fidelity;
  modelUsed?: string;
};

export async function chatWithClone(
  personaId: string,
  message: string,
  history: ChatTurn[] = [],
  channel: Channel = "chat",
  tone?: Partial<Tone>,
): Promise<ChatWithCloneResult> {
  return fetchJson<ChatWithCloneResult>("/api/mirror/chat", {
    method: "POST",
    body: JSON.stringify({
      personaId,
      message,
      history,
      channel,
      tone: tone
        ? {
            formality: tone.formality,
            hinglish: tone.hinglish,
          }
        : null,
    }),
  });
}

export async function fetchVoiceKb(personaId: string): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>("/api/mirror/voice-kb", {
    method: "POST",
    body: JSON.stringify({ personaId }),
  });
}

export async function fetchPersonaCapsule(
  id: string,
): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>(`/api/personas/${id}/capsule`);
}

/* -------------------------------------------------------------------------- */
/* React Query hooks                                                          */
/* -------------------------------------------------------------------------- */

export function usePersonas() {
  return useQuery({ queryKey: keys.personas, queryFn: fetchPersonas });
}

export function usePersona(id: string) {
  return useQuery({
    queryKey: keys.persona(id),
    queryFn: () => fetchPersona(id),
    enabled: Boolean(id),
  });
}

export function usePersonaCapsule(id: string) {
  return useQuery({
    queryKey: [...keys.persona(id), "capsule"] as const,
    queryFn: () => fetchPersonaCapsule(id),
    enabled: Boolean(id),
  });
}

export function useCreatePersona(
  options?: UseMutationOptions<Persona, Error, { name: string; languagePrimary?: string }>,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: createPersona,
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.personas });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useUpdatePersona(
  options?: UseMutationOptions<
    Persona,
    Error,
    { id: string; name?: string; languagePrimary?: string }
  >,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: ({ id, ...body }) => updatePersona(id, body),
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.personas });
      qc.invalidateQueries({ queryKey: keys.persona(vars.id) });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useDeletePersona(
  options?: UseMutationOptions<void, Error, string>,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: deletePersona,
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.personas });
      qc.removeQueries({ queryKey: keys.persona(vars) });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useConversations() {
  return useQuery({ queryKey: keys.conversations, queryFn: fetchConversations });
}

export function useConversationMessages(id: string) {
  return useQuery({
    queryKey: keys.messages(id),
    queryFn: () => fetchConversationMessages(id),
    enabled: Boolean(id),
  });
}

export function useCreateConversation(
  options?: UseMutationOptions<Conversation, Error, { personaId: string; channel?: Channel }>,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: createConversation,
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.conversations });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useCaptureWriting(
  options?: UseMutationOptions<CaptureMirrorResult, Error, { text: string; sourceType?: string }>,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: ({ text, sourceType }) => captureWriting(text, sourceType),
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.personas });
      if (data.personaId) {
        qc.invalidateQueries({ queryKey: keys.persona(data.personaId) });
      }
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useCaptureToPersona(
  options?: UseMutationOptions<
    CaptureToPersonaResult,
    Error,
    { personaId: string; text: string; sourceType?: string }
  >,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: ({ personaId, text, sourceType }) => captureToPersona(personaId, text, sourceType),
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.persona(vars.personaId) });
      qc.invalidateQueries({ queryKey: keys.personas });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useChatWithClone(
  options?: UseMutationOptions<
    ChatWithCloneResult,
    Error,
    {
      personaId: string;
      message: string;
      history?: ChatTurn[];
      channel?: Channel;
      tone?: Partial<Tone>;
    }
  >,
) {
  const qc = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: ({ personaId, message, history, channel, tone }) =>
      chatWithClone(personaId, message, history, channel, tone),
    onSuccess: (data, vars, ctx, mutationCtx) => {
      qc.invalidateQueries({ queryKey: keys.conversations });
      options?.onSuccess?.(data, vars, ctx, mutationCtx);
    },
  });
}

export function useVoiceKb(
  options?: UseMutationOptions<Record<string, unknown>, Error, string>,
) {
  return useMutation({
    ...options,
    mutationFn: fetchVoiceKb,
  });
}
