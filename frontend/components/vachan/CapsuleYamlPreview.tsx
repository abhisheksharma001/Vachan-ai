"use client";

import { useState } from "react";
import styles from "./CapsuleYamlPreview.module.css";

const SAMPLE_YAML = `version: 12
confidence: 0.84
evidence_tokens: 14200
last_calibrated: 2 hours ago

steering:
  warmth: 0.62
  directness: 0.51
  formality: 0.40
  hinglish: 0.33

language:
  cmi_target: 0.33
  script: "roman"
  auto_detect: true

do:
  - "use yaar with peers"
  - "keep replies under 3 sentences"

dont:
  - "use formal Hindi with elders"
  - "promise deadlines without checking"

provenance:
  sources:
    - type: paste
      tokens: 4200
    - type: whatsapp_export
      tokens: 10000
`;

export function CapsuleYamlPreview({ personaId }: { personaId: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(SAMPLE_YAML);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className={styles.card}>
      <div className={styles.head}>
        <div>
          <span className="label">Capsule preview</span>
          <p className={styles.sub}>Read-only YAML view of the structured record.</p>
        </div>
        <button type="button" className={styles.copyBtn} onClick={copy}>
          {copied ? "Copied ✓" : "Copy YAML"}
        </button>
      </div>
      <pre className={styles.pre} aria-label="Persona capsule YAML preview">
        <code>{SAMPLE_YAML}</code>
      </pre>
      <p className={styles.foot}>
        The structured record is the source of truth. YAML editing requires
        validation + a preview diff. Persona ID: {personaId}
      </p>
    </div>
  );
}
