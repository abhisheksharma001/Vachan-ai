# Control-vector spike — Hinglish tone dial (Kaggle)

The V2 thesis in one notebook: shift a model's tone (formal English ↔ casual
Hinglish) by **adding a direction to its hidden states at generation time** — no
fine-tuning, no retraining. If this works, it's the path beyond prompt-steering.

**File:** [`hinglish_control_vector_kaggle.ipynb`](hinglish_control_vector_kaggle.ipynb)
**Model:** Llama-3.1-8B (4-bit) · **Hardware:** one Kaggle T4 (free) · **Time:** ~5–10 min

---

## How Kaggle "connects" to this repo

Short version: **it doesn't auto-sync, and for this spike it doesn't need to.**
Kaggle runs in its own throwaway cloud box. The notebook is **standalone** — it
pulls Llama from HuggingFace and runs `repeng`; it never touches the Vachan
backend, the DB, or your API keys. You just need to get the `.ipynb` file *onto*
Kaggle. Three ways, easiest first:

### Option A — Upload the file (simplest, recommended)
1. Download [`hinglish_control_vector_kaggle.ipynb`](hinglish_control_vector_kaggle.ipynb)
   from GitHub (open it → **⋯ → Download**, or `Raw → Save As`).
2. Go to <https://www.kaggle.com/code> → **New Notebook** → **File → Import Notebook** → upload it.

### Option B — Import straight from GitHub
1. Kaggle → **New Notebook** → **File → Import Notebook → from URL** (GitHub tab).
2. Paste the file URL. *(This repo is **private**, so the public-URL import won't
   see it — keep it public-link-only for now or use Option A. Once the repo is
   public, this just works.)*

### Option C — Clone the repo inside the notebook (only when you need Vachan code)
Not needed for the spike. When a later notebook *does* need the persona capsules:
add a GitHub token in Kaggle **Add-ons → Secrets** as `GH_TOKEN`, then
```python
from kaggle_secrets import UserSecretsClient
tok = UserSecretsClient().get_secret("GH_TOKEN")
!git clone https://{tok}@github.com/abhisheksharma001/Vachan-ai.git
```

---

## Before you hit Run

1. **GPU on:** right panel → **Accelerator → GPU T4 x2** (or T4). Without this it
   runs on CPU and will crawl.
2. **Internet on:** Settings → **Internet → On** (needed to download the model).
3. **HF token:** *not required* — the notebook uses a non-gated Llama mirror. (If
   you switch to Meta's official `meta-llama/Llama-3.1-8B-Instruct`: accept its
   license on HF, make a read token, add it in Kaggle **Add-ons → Secrets** as
   `HF_TOKEN`.)
4. **Run All.**

## What you should see

Same prompt, three settings of the dial:

```
=== coeff -2 ===  The deployment has been completed successfully. Please find the status below...
=== coeff  0 ===  (the untouched model — somewhere in between)
=== coeff +2 ===  haan bhai deployment ho gaya, abhi testing chal rahi hai, thoda ruk ja...
```

If the tone moves with the number, the thesis holds.

## If it misbehaves
- **Text turns to garbage** at high coeff → drop to `1.0`–`2.0`.
- **Effect too weak** → widen the layer band in the `ControlModel(...)` line to
  `range(-3, -22, -1)`, or add more contrastive pairs.
- **OOM** → you're not on GPU, or another notebook is holding the card; restart
  the session.

## Next, after the spike proves out
1. **Per-persona vector** — build the contrast from a persona's *own* anchors
   (their Hinglish vs the English-translated anchors we already store) → a
   personalized dial.
2. **Serving** — control vectors need *our* forward pass (Groq can't inject), so
   the steered model runs behind vLLM/transformers on a serverless GPU, only for
   high-value personas the PFS gate keeps failing (the documented Path-B trigger).
3. **Objective** — tune the coefficient against the Fidelity Ring's neural cosine.
