/*
 * GET  /api/conversations     — list conversations.
 * POST /api/conversations     — create a new conversation for a persona.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function GET() {
  try {
    const res = await backend("/conversations", { method: "GET" });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not list conversations.", detail: await res.text() },
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

export async function POST(req: NextRequest) {
  let body: { personaId?: string; channel?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  if (!body.personaId) {
    return NextResponse.json(
      { error: "Missing personaId." },
      { status: 400 },
    );
  }

  try {
    const res = await backend("/conversations", {
      method: "POST",
      body: JSON.stringify({
        persona_id: body.personaId,
        channel: body.channel ?? "chat",
      }),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not create conversation.", detail: await res.text() },
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
