/*
 * POST /api/mirror/chat — the BFF for chatting with your clone.
 *
 * Forwards the message (+ prior turns + live slider tone) to the persona chat
 * endpoint, which renders an in-voice reply and scores its fidelity. Passes the
 * reply + the Fidelity Ring data straight back to the browser.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

type Turn = { role: "user" | "clone"; content: string };
type Tone = { formality?: number; hinglish?: number };

export async function POST(req: NextRequest) {
  let body: {
    personaId?: string;
    message?: string;
    history?: Turn[];
    tone?: Tone;
    channel?: string;
    isCorrection?: boolean;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const message = (body.message ?? "").trim();
  if (!body.personaId || !message) {
    return NextResponse.json({ error: "Missing personaId or message." }, { status: 400 });
  }

  try {
    const res = await backend(`/personas/${body.personaId}/chat`, {
      method: "POST",
      body: JSON.stringify({
        message,
        history: body.history ?? [],
        tone: body.tone ?? null,
        channel: body.channel ?? "chat",
        score: true,
        is_correction: body.isCorrection ?? false,
      }),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Your clone could not reply.", detail: await res.text() },
        { status: 502 },
      );
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Backend unreachable." },
      { status: 502 },
    );
  }
}
