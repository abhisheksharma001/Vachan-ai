"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Slider } from "@/components/ui/Slider";
import styles from "./CapsuleForm.module.css";

export function CapsuleForm({ personaId }: { personaId: string }) {
  const [name, setName] = useState("Aakash (work)");
  const [description, setDescription] = useState("Professional voice for client and vendor comms.");
  const [formality, setFormality] = useState(40);
  const [hinglish, setHinglish] = useState(33);
  const [dos, setDos] = useState(["use yaar with peers", "keep replies under 3 sentences"]);
  const [donts, setDonts] = useState(["use formal Hindi with elders", "promise deadlines without checking"]);

  return (
    <form className={styles.card} onSubmit={(e) => e.preventDefault()}>
      <div className={styles.head}>
        <div>
          <span className="label">Identity</span>
          <p className={styles.sub}>What this voice is for.</p>
        </div>
      </div>

      <div className={styles.group}>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>Name</span>
          <input
            className={styles.input}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>Description</span>
          <textarea
            className={styles.textarea}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
      </div>

      <div className={styles.divider} />

      <div className={styles.head}>
        <div>
          <span className="label">Tone steering</span>
          <p className={styles.sub}>Drag to adjust how this voice sounds.</p>
        </div>
      </div>

      <div className={styles.group}>
        <label htmlFor="formality" className={styles.field}>
          <div className={styles.sliderLabel}>
            <span className={styles.fieldLabel}>Formality</span>
            <span className={styles.sliderValue}>{formality}%</span>
          </div>
          <Slider
            id="formality"
            min={0}
            max={100}
            value={formality}
            onChange={(e) => setFormality(Number(e.target.value))}
          />
        </label>
        <label htmlFor="hinglish" className={styles.field}>
          <div className={styles.sliderLabel}>
            <span className={styles.fieldLabel}>Hinglish mix</span>
            <span className={styles.sliderValue}>{hinglish}%</span>
          </div>
          <Slider
            id="hinglish"
            min={0}
            max={100}
            value={hinglish}
            onChange={(e) => setHinglish(Number(e.target.value))}
          />
        </label>
      </div>

      <div className={styles.divider} />

      <div className={styles.head}>
        <div>
          <span className="label">Do / Don&apos;t</span>
          <p className={styles.sub}>Hard rules the clone follows.</p>
        </div>
      </div>

      <div className={styles.group}>
        <div className={styles.ruleBlock}>
          <span className={styles.ruleTitle}>Do</span>
          <div className={styles.chips}>
            {dos.map((d) => (
              <span key={d} className={styles.chipDo}>{d}</span>
            ))}
            <button type="button" className={styles.addChip}>+ Add</button>
          </div>
        </div>
        <div className={styles.ruleBlock}>
          <span className={styles.ruleTitle}>Don&apos;t</span>
          <div className={styles.chips}>
            {donts.map((d) => (
              <span key={d} className={styles.chipDont}>{d}</span>
            ))}
            <button type="button" className={styles.addChip}>+ Add</button>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <Button type="submit" variant="primary">
          Save changes
        </Button>
      </div>
      <input type="hidden" value={personaId} readOnly />
    </form>
  );
}
