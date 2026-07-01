import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

/**
 * POST /api/ghostwriter/rewrite
 *
 * Scaffold for the Ghostwriter approval queue. In production this calls the
 * tone engine to draft a reply in the user's voice. For now it returns a
 * fallback draft so the UI can be wired and tested end-to-end.
 */
export async function POST(req: NextRequest) {
  let body: { personaId?: string; incoming?: string; tone?: Record<string, number> };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const personaId = body.personaId;
  const incoming = (body.incoming ?? "").trim();

  if (!personaId) {
    return NextResponse.json({ error: "personaId is required." }, { status: 400 });
  }
  if (!incoming) {
    return NextResponse.json({ error: "incoming message is required." }, { status: 400 });
  }

  try {
    // Attempt a real backend call; if it 404s, fall back to a safe scaffold.
    const res = await backend(`/personas/${personaId}/ghostwriter`, {
      method: "POST",
      body: JSON.stringify({ incoming, tone: body.tone }),
    });

    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Backend endpoint not ready — use fallback below.
  }

  return NextResponse.json({
    draft: `haan, iske baare mein baat karte hain — main aapke tone mein ek reply draft kar deta hu.\n\n"Thanks for flagging. Let's discuss this on a quick call tomorrow — I'll share the details then."`,
    fidelity: 0.82,
    tone: "polite Hinglish",
  });
}
