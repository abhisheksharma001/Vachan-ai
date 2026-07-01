import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/capture/preview
 *
 * Returns a sanitization preview of the user's text. In production this calls
 * the backend Presidio + Indian-pattern PII service. Here we provide a safe
 * client-side regex fallback so the UI always has a preview to show.
 */
export async function POST(req: NextRequest) {
  let body: { text?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const text = (body.text ?? "").trim();
  if (!text) {
    return NextResponse.json({ error: "No text provided." }, { status: 400 });
  }

  const entities = new Set<string>();
  let sanitized = text;

  // Phone numbers (Indian +91 and generic mobile).
  sanitized = sanitized.replace(/(\+91[\s-]?)?[6-9]\d{9}/g, (m) => {
    entities.add("Phone numbers");
    return "[IN_PHONE]";
  });

  // Emails.
  sanitized = sanitized.replace(/[\w.-]+@[\w.-]+\.\w+/g, (m) => {
    entities.add("Emails");
    return "[EMAIL]";
  });

  // UPI IDs.
  sanitized = sanitized.replace(/[\w.-]+@[\w]+/g, (m) => {
    if (m.includes("@ok") || m.includes("@paytm") || m.includes("@upi") || m.includes("@ybl")) {
      entities.add("UPI IDs");
      return "[UPI_ID]";
    }
    return m;
  });

  // Aadhaar (12 digits, optional spaces).
  sanitized = sanitized.replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, (m) => {
    entities.add("Aadhaar/PAN");
    return "[AADHAAR]";
  });

  // PAN.
  sanitized = sanitized.replace(/\b[A-Z]{5}\d{4}[A-Z]\b/g, (m) => {
    entities.add("Aadhaar/PAN");
    return "[PAN]";
  });

  return NextResponse.json({
    sanitized,
    entities: Array.from(entities),
  });
}
