/*
 * Server-only backend client for the Mirror BFF (route handlers in app/api/*).
 *
 * Why this exists: the browser never talks to the FastAPI backend directly.
 * These helpers run on the Next.js SERVER, mint a short-lived DEV token via the
 * backend's /auth/dev-token issuer, and attach it as a Bearer header. So:
 *   • the auth secret + token never reach the browser (no token in client JS),
 *   • there is no CORS to configure (server-to-server over localhost).
 *
 * n8n analogy: a "credential" attached on a backend HTTP node — the front-end
 * trigger never sees it.
 *
 * The dev identity is FIXED so a capture and its follow-up chats land in the
 * same tenant (Row-Level Security pins every row to this org). Local dev only —
 * /auth/dev-token 404s in production, where a managed provider issues tokens.
 *
 * NOTE: this module must only be imported from server code (route handlers in
 * app/api/*). It is never imported by a client component, so the dev token and
 * backend URL never reach the browser.
 */
// 127.0.0.1 (not "localhost") forces IPv4 — on machines where localhost
// resolves to IPv6 ::1 first, that can hit the wrong listener. Override with
// the BACKEND_URL env var if the backend runs elsewhere.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

// Stable dev tenant for the local Mirror (valid UUIDs; JIT-provisioned on use).
const DEV_ORG_ID = "00000000-0000-4000-8000-0000000000a1";
const DEV_USER_ID = "00000000-0000-4000-8000-0000000000b1";
const DEV_EMAIL = "mirror@dev.local";

async function devToken(): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/auth/dev-token`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ user_id: DEV_USER_ID, org_id: DEV_ORG_ID, email: DEV_EMAIL }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `dev-token failed (${res.status}). Is the backend running at ${BACKEND_URL} with AUTH_MODE=dev?`,
    );
  }
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

/** Call the FastAPI backend with a fresh dev Bearer token attached. */
export async function backend(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await devToken();
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
}

export { BACKEND_URL };
