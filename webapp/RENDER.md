# Deploy MosquitoScope on Render (model on Hugging Face)

## Overview

| Piece | Where |
|-------|--------|
| **Code** | GitHub |
| **Model (~107 MB)** | Hugging Face Hub (public model repo) |
| **Web app** | Render (Docker) |

---

## Step 1 — Upload model to Hugging Face (one time)

1. Create a free account at [huggingface.co](https://huggingface.co/join).
2. Create an access token: **Settings → Access Tokens → New token** (Read is enough for public repos; Write for upload).
3. Log in on this machine:

```bash
huggingface-cli login
# paste your Write token
```

4. Upload the checkpoint (replace `YOUR_USERNAME`):

```bash
cd /home/st1992@unt.ad.unt.edu/mosquitos
python scripts/upload_model_to_hf.py \
  --repo-id YOUR_USERNAME/mosquitoscope-convnextv2-tiny
```

This creates a **public** model repo with:
- `mosquito_convnextv2_tiny_final.pth`
- `test_metrics.json`
- `README.md` (model card)

Note the repo id, e.g. `YOUR_USERNAME/mosquitoscope-convnextv2-tiny`.

---

## Step 2 — Push code to GitHub

```bash
cd /home/st1992@unt.ad.unt.edu/mosquitos
git init
git add webapp/ render.yaml README.md .gitignore scripts/upload_model_to_hf.py
git commit -m "MosquitoScope webapp with Render + Hugging Face model hosting"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mosquitoscope.git
git push -u origin main
```

Do **not** commit `Data/` or `*.pth` files.

---

## Step 3 — Deploy on Render

1. [render.com](https://render.com) → sign in with GitHub.
2. **New → Blueprint** → select your repo (uses `render.yaml`).
3. When prompted, set:

| Variable | Example |
|----------|---------|
| `HF_MODEL_REPO` | `YOUR_USERNAME/mosquitoscope-convnextv2-tiny` |

(`FORCE_CPU` and `TORCH_NUM_THREADS` are already set in `render.yaml`.)

4. Choose **Starter** instance (~$7/mo) if free tier runs out of memory.
5. Deploy and wait ~5–10 minutes (Docker build + model download from HF).

Your public URL: `https://mosquitoscope.onrender.com` (or the name you pick).

---

## Step 4 — Share with students

Send them the Render URL. No tunnel or laptop required.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Upload fails | Run `huggingface-cli login` with a **Write** token |
| Model not found on Render | Check `HF_MODEL_REPO` matches the HF repo exactly |
| Out of memory | Upgrade to Starter plan on Render |
| Slow first load | Free tier sleeps; first visit wakes the service (~30–60s) |

---

## Local production test

```bash
cd webapp
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
export HF_MODEL_REPO=YOUR_USERNAME/mosquitoscope-convnextv2-tiny
export FORCE_CPU=1
./entrypoint.sh
```
