/*
 * POST /api/mirror/voice-kb — the BFF for the voice knowledge-base export.
 *
 * Vachan doesn't run STT/TTS; it hands an external voice platform (Vapi, Retell,
 * LiveKit…) a paste-ready voice system prompt + guidelines compiled from the
 * persona. This forwards to the backend's GET /personas/{id}/voice-kb.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function POST(req: NextRequest) {
  let body: { personaId?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }
  if (!body.personaId) {
    return NextResponse.json({ error: "Missing personaId." }, { status: 400 });
  }

  try {
    const res = await backend(`/personas/${body.personaId}/voice-kb`, { method: "GET" });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not build the voice KB.", detail: await res.text() },
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
