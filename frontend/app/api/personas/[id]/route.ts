/*
 * GET   /api/personas/{id} — fetch a persona.
 * PATCH /api/personas/{id} — update a persona's name / language.
 * DELETE /api/personas/{id} — soft-delete a persona.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    const res = await backend(`/personas/${params.id}`, { method: "GET" });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not fetch persona.", detail: await res.text() },
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

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } },
) {
  let body: { name?: string; language_primary?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  if (!body.name && !body.language_primary) {
    return NextResponse.json(
      { error: "Provide name or language_primary to update." },
      { status: 400 },
    );
  }

  try {
    const res = await backend(`/personas/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not update persona.", detail: await res.text() },
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

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    const res = await backend(`/personas/${params.id}`, { method: "DELETE" });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not delete persona.", detail: await res.text() },
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
