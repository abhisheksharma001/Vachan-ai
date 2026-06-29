# Control Vectors — Vachan V2 Tone Dial

This folder contains Kaggle-runnable spike notebooks that prove out the control-vector path for Vachan V2.

## Notebooks

| Notebook | What it proves | Status |
|---|---|---|
| `hinglish_control_vector_kaggle.ipynb` | Generic Hinglish ↔ English tone dial works — coeff moves tone | ✅ merged (PR #3) |
| `per_persona_control_vector_kaggle.ipynb` | Persona-anchored vector — dial is tuned to one person's real voice | ⬅ run this next |

## How to run on Kaggle

1. Open the notebook on GitHub → Download `.ipynb`
2. [kaggle.com/code](https://www.kaggle.com/code) → New Notebook → File → Import Notebook → upload it
3. Right panel: **Accelerator → GPU T4** · **Internet → On** → **Run All**

No HuggingFace token needed.

## How the per-persona notebook works

The basic spike used a fixed system-prompt contrast (WhatsApp friend vs corporate email).  
The per-persona notebook replaces that with **the persona's own anchor phrases**:

```
Positive anchors  →  real Hinglish samples this persona uses
Negative anchors  →  clean English translations of the same ideas
Vector            =  difference in hidden state between the two lists
```

Output: a `.pt` file (the vector) + a `.json` config (recommended coeff, av_cosine score).  
One file pair per persona. Load at inference; no re-training.

## Fidelity Ring integration

The notebook uses `all-MiniLM-L6-v2` embeddings — same family as the Fidelity Ring — so `av_cosine` scores are directly comparable.

Target thresholds (same as main system):
- `av_cosine ≥ 0.70` → persona voice holding, no vector needed
- `av_cosine < 0.60` → apply vector at `recommended_coeff` from config

## Production path (post-spike)

1. **Store** `{persona}_tone_vector.pt` + `{persona}_vector_config.json` in object storage
2. **Load** in a vLLM/transformers worker (can't use Groq — Groq doesn't expose hidden states)
3. **Trigger** when Fidelity Ring drift gate fires → apply vector → re-score
4. **Adaptive dial** (later): binary-search coeff until av_cosine ≥ 0.70

## Layer band

Both notebooks target `range(-5, -18, -1)` — the middle/late transformer layers where stylistic representation lives.  
If the effect is weak, widen to `range(-3, -22, -1)`.
