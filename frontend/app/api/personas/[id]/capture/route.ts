/*
 * POST /api/personas/{id}/capture — capture writing into an existing persona.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } },
) {
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
    const res = await backend(`/personas/${params.id}/capture`, {
      method: "POST",
      body: JSON.stringify({
        source_type: body.sourceType ?? "paste",
        text,
        build_capsule: true,
      }),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Capture failed.", detail: await res.text() },
        { status: 502 },
      );
    }
    const capture = (await res.json()) as Record<string, unknown>;

    return NextResponse.json({
      band: capture.band,
      stored: capture.stored,
      totalTokens: capture.total_tokens,
      style: capture.style,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Backend unreachable." },
      { status: 502 },
    );
  }
}
