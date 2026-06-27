/*
 * POST /api/mirror/capture  — the BFF for "paste your writing → build a clone".
 *
 * Creates a fresh persona, captures the pasted text (PII-sanitized + measured +
 * a capsule projected, all server-side), then reads the capsule back so the
 * Mirror can seed its Tonality Sliders. Returns just what the UI needs.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function POST(req: NextRequest) {
  let body: { text?: string; sourceType?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const text = (body.text ?? "").trim();
  if (text.length < 20) {
    return NextResponse.json(
      { error: "Paste a little more — a few of your real messages work best." },
      { status: 400 },
    );
  }

  try {
    // 1) a fresh persona (this also records the DPDP consent to model you)
    const pRes = await backend("/personas", {
      method: "POST",
      body: JSON.stringify({ name: "My Mirror" }),
    });
    if (!pRes.ok) {
      return NextResponse.json(
        { error: "Could not create a persona.", detail: await pRes.text() },
        { status: 502 },
      );
    }
    const { persona_id: personaId } = (await pRes.json()) as { persona_id: string };

    // 2) capture + project the capsule
    const cRes = await backend(`/personas/${personaId}/capture`, {
      method: "POST",
      body: JSON.stringify({
        source_type: body.sourceType ?? "paste",
        text,
        build_capsule: true,
      }),
    });
    if (!cRes.ok) {
      return NextResponse.json(
        { error: "Capture failed.", detail: await cRes.text() },
        { status: 502 },
      );
    }
    const capture = (await cRes.json()) as Record<string, unknown>;

    // 3) read the capsule back (language + steering seed the sliders)
    const capRes = await backend(`/personas/${personaId}/capsule`, { method: "GET" });
    const capsule = capRes.ok ? await capRes.json() : null;

    return NextResponse.json({
      personaId,
      band: capture.band,
      stored: capture.stored,
      totalTokens: capture.total_tokens,
      style: capture.style,
      capsuleData: capsule?.capsule_data ?? null,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Backend unreachable." },
      { status: 502 },
    );
  }
}
