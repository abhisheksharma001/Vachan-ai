import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/capture/build
 *
 * Proxies to the existing /api/mirror/capture BFF so the capture page and the
 * Mirror share the same build logic.
 */
export async function POST(req: NextRequest) {
  const body = await req.text();
  const res = await fetch(new URL("/api/mirror/capture", req.url), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });

  const data = await res.json().catch(() => ({ error: "Invalid upstream response." }));
  return NextResponse.json(data, { status: res.status });
}
