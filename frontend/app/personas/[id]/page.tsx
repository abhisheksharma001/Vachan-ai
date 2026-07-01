"use client";

import { useState } from "react";
import { PersonaHeader } from "@/components/vachan/PersonaHeader";
import { CapsuleForm } from "@/components/vachan/CapsuleForm";
import { CapsuleYamlPreview } from "@/components/vachan/CapsuleYamlPreview";
import { VersionTimeline } from "@/components/vachan/VersionTimeline";
import styles from "./page.module.css";

const TABS = [
  { id: "edit", label: "Edit capsule" },
  { id: "preview", label: "YAML preview" },
  { id: "history", label: "History" },
];

export default function PersonaDetailPage({ params }: { params: { id: string } }) {
  const [tab, setTab] = useState("edit");

  return (
    <div className={styles.page}>
      <PersonaHeader personaId={params.id} />

      <nav className={styles.tabs} aria-label="Persona sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`${styles.tab} ${tab === t.id ? styles.tabActive : ""}`}
            onClick={() => setTab(t.id)}
            aria-current={tab === t.id ? "page" : undefined}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className={styles.main}>
        {tab === "edit" && (
          <div className={styles.layout}>
            <CapsuleForm personaId={params.id} />
            <CapsuleYamlPreview personaId={params.id} />
          </div>
        )}
        {tab === "preview" && (
          <div className={styles.single}>
            <CapsuleYamlPreview personaId={params.id} />
          </div>
        )}
        {tab === "history" && <VersionTimeline personaId={params.id} />}
      </main>
    </div>
  );
}
