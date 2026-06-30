/*
 * GET  /api/personas — list personas for the authenticated dev tenant.
 * POST /api/personas — create a new persona.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function GET() {
  try {
    const res = await backend("/personas", { method: "GET" });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not list personas.", detail: await res.text() },
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
  let body: { name?: string; language_primary?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  if (!body.name) {
    return NextResponse.json({ error: "Missing name." }, { status: 400 });
  }

  try {
    const res = await backend("/personas", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not create persona.", detail: await res.text() },
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
