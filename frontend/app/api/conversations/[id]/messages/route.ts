/*
 * GET /api/conversations/{id}/messages — fetch a conversation's message history.
 */
import { NextRequest, NextResponse } from "next/server";

import { backend } from "@/lib/backend";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    const res = await backend(`/conversations/${params.id}/messages`, {
      method: "GET",
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Could not load messages.", detail: await res.text() },
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
