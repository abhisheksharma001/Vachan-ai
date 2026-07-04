export type Channel = "chat" | "english" | "email" | "voice";
export type Role = "user" | "clone";

export interface Persona {
  id: string;
  name: string;
  status: string;
  languagePrimary: string;
  currentCapsuleVersion: number;
  createdAt: string;
  observationsCount: number;
}

export interface Conversation {
  conversationId: string;
  personaId: string;
  personaName: string;
  channel: Channel;
  capsuleVersion: number;
  startedAt: string;
  lastActiveAt: string;
  turnCount: number;
}

export interface Message {
  turnNumber: number;
  role: Role;
  content: string;
  pfsScore: number | null;
  modelUsed: string;
  createdAt: string;
}

export interface Fidelity {
  pfs: number | null;
  pfsBasis?: string;
  judgeScore?: number | null;
  judgeReason?: string;
  cmiOutput?: number | null;
  cmiTarget?: number | null;
  hardRulePass?: boolean;
  hardRuleViolations?: string[];
  avCosine?: number | null;
  centroidDistance?: number | null;
  pacingMatch?: number | null;
}

export interface Tone {
  warmth: number;
  directness: number;
  formality: number;
  hinglish: number;
}
