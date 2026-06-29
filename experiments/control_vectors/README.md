# Control Vectors — Vachan V2 Tone Dial

This folder contains the spike and per-persona notebooks for Vachan's V2 tone-steering path. Control vectors let us shift the model's tone at generation time — no fine-tuning, no retraining.

---

## Notebooks

| Notebook | Purpose | Status |
|---|---|---|
| `hinglish_control_vector_kaggle.ipynb` | Basic spike — proves the Hinglish↔English axis works with generic contrastive prompts | ✅ Merged (PR #3) |
| `per_persona_control_vector_kaggle.ipynb` | Builds the tone dial from a **real persona's own anchor phrases** — one vector per persona | 🔄 In review |

---

## How to Run on Kaggle

1. Open the notebook on GitHub → Download raw `.ipynb`
2. [kaggle.com/code](https://www.kaggle.com/code) → New Notebook → File → Import Notebook → upload
3. Right panel: **Accelerator → GPU T4**, **Internet → On**
4. **Run All** (~5–12 min)

No HuggingFace token needed — both notebooks use the non-gated `NousResearch/Meta-Llama-3.1-8B-Instruct` mirror.

---

## What a Control Vector Is

A control vector is a single direction in the model's hidden-state space. We find it by showing the model the same situation described two ways (positive pole vs negative pole) and subtracting the two internal activation patterns. That difference *is* the tone axis.

At generation time: `hidden_state += coeff × vector`
- `coeff > 0` → push toward positive pole (Hinglish / persona tone)
- `coeff < 0` → push toward negative pole (formal English)
- `coeff = 0` → untouched model

---

## Per-Persona Vectors (what the second notebook adds)

Instead of a generic Hinglish axis, the per-persona notebook builds the contrast from **a real persona's own anchor phrases** — the Hinglish messages they actually use, paired with their English-translated equivalents.

This means:
- Rahul's vector captures his slang ("yaar kya scene hai")
- Priya's vector captures her lighter code-mix style
- The dial is personalized, not generic

### Persona-Specificity Check
The notebook measures cosine similarity between persona vectors at a representative layer. Target: < 0.80 between any two personas. High similarity (> 0.90) means the anchors need to be more distinctive.

---

## Output Files

The per-persona notebook saves one `.pt` file per persona to `/kaggle/working/persona_vectors/`:

```
persona_vectors/
  rahul_tone_vector.pt
  priya_tone_vector.pt
  ankit_tone_vector.pt
```

Download these from the Kaggle output panel. In production, the serving layer loads these at startup, keyed by `persona_id`.

---

## Path into Production (Later Sprints)

```
Fidelity Ring reads av_cosine
       ↓
av_cosine < threshold for persona X
       ↓
Switch Groq → local model (vLLM / transformers)
Load vectors[persona_X]
Set coeff via fidelity reading
Generate with tone dial active
       ↓
Fidelity Ring re-scores → coeff tuned over time
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|---|
| `repeng` import error | Run the `!pip install` cell first, then restart kernel |
| `bitsandbytes` CUDA error | Confirm GPU T4 is selected in Kaggle accelerator panel |
| Gibberish at high coeff | Back off to `coeff 1.5`; 4-bit quant is more sensitive |
| Weak tone shift | Widen layer band to `range(-3, -22, -1)` or add more anchor pairs |
| Persona vectors too similar (cosine > 0.90) | Add 16–24 anchors per persona; use more distinctive phrases |
