/*
 * POST /api/personas/sanitize-preview — BFF for redaction preview.
 *
 * Returns the original text, the sanitized version, and the redacted spans so
 * the Capture tab can show the user exactly what private details will be
 * removed before storage.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function POST(req: NextRequest) {
  let body: { text?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const text = (body.text ?? "").trim();
  if (!text) {
    return NextResponse.json({ error: "Missing text." }, { status: 400 });
  }

  try {
    const res = await backend("/personas/sanitize-preview", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not preview redaction.", detail: await res.text() },
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
