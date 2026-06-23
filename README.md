# MosquitoScope

AI-powered **41-class mosquito species classifier** with a Flask web demo. Trained with a **hybrid class-weighted recipe** (sqrt-balanced focal loss, MixUp, RandAugment, cosine LR, TTA) on ConvNeXt V2 Tiny at 288px.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/pytorch-2.0%2B-red)
![Test accuracy](https://img.shields.io/badge/test%20accuracy-74.0%25-green)
![Classes](https://img.shields.io/badge/species-41-orange)

---

## Results (latest — expanded dataset)

Trained on **1,536 images** (41 species, ≥20 images/class) → **1,228 train / 308 test**.

| Method | Dataset | CV accuracy | Test accuracy | Test F1 (macro) |
|--------|---------|-------------|---------------|-----------------|
| Baseline (unweighted CE) | 1,081 imgs | 59.4% | 66.8% | 62.0% |
| Full balanced weights | 1,081 imgs | ~59.5% | — | ~52.4% (CV) |
| **Hybrid (production)** | 1,081 imgs | 69.0% | 72.8% | 69.4% |
| **Hybrid (production)** | **1,536 imgs** | **73.9%** | **74.0%** | **70.6%** |

**Production model:** `results_class_weight/final/mosquito_convnextv2_tiny_final.pth`

| Metric | Value |
|--------|-------|
| Test accuracy (TTA) | **74.03%** |
| Precision (macro) | 73.55% |
| Recall (macro) | 70.68% |
| F1 (macro) | **70.60%** |
| F1 (weighted) | 73.47% |
| CV mean accuracy | 73.86% ± 1.7% |
| Best trial | lr=5e-5, batch=8, wd=0.01, 24 epochs |

---

## Features

### Web app (`webapp/`)

- Upload or drag-and-drop mosquito images
- Top-5 predictions with confidence ring
- Species profile (taxonomy, diseases, risk, biting behavior)
- Clickable disease tags with CDC/WHO links
- Optional ground-truth comparison against test-set per-class metrics

### Training pipeline

- 5-fold stratified CV + 12-trial hyperparameter grid search
- Hybrid loss: **sqrt-balanced class weights + focal loss + label smoothing**
- Strong augmentation: RandomResizedCrop, RandAugment, MixUp
- AdamW + cosine schedule with warmup
- Final training on full train split + held-out test evaluation with TTA

---

## Quick start (web demo)

### Prerequisites

- Python 3.10+
- CUDA GPU recommended (CPU works but slower)
- Trained checkpoint at `results_class_weight/final/mosquito_convnextv2_tiny_final.pth`

### Install

```bash
git clone <your-repo-url>
cd mosquitos

pip install torch torchvision timm flask pillow scikit-learn matplotlib gdown
# or webapp only:
pip install -r webapp/requirements.txt
```

### Run the web app

```bash
cd webapp
python app.py
```

Open **http://localhost:7860**

Health check:

```bash
curl http://localhost:7860/health
```

Expected response includes `num_classes: 41`, `image_size: 288`, `training_recipe: v2_enhanced_memsafe`.

### Share with students (optional — public URL)

On another machine or network, expose port 7860 with a tunnel:

```bash
# Terminal 1 — app
cd webapp && python app.py

# Terminal 2 — public link (requires SSH)
ssh -R 80:localhost:7860 nokey@localhost.run
```

Share the `https://….lhr.life` URL printed in the terminal.

### Deploy on Render (persistent hosting)

Model weights live on **Hugging Face Hub**; the web app runs on **Render**.

1. Upload the checkpoint: `python scripts/upload_model_to_hf.py --repo-id YOUR_USERNAME/mosquitoscope-convnextv2-tiny` (after `huggingface-cli login`)
2. Push this repo to GitHub (no `.pth` in git)
3. Render → Blueprint → set `HF_MODEL_REPO` to your HF model repo

Full steps: **[webapp/RENDER.md](webapp/RENDER.md)**.

---

## Dataset setup

Images must be organized **one folder per species**:

```
Data/
└── Data/
    └── Mosquito Images/
        ├── Aedes_aegypti/
        ├── Culex_quinequefasciatus/
        └── ... (species folders)
```

### Download (notebook cell 1)

The notebook downloads from Google Drive if `Data/` is empty. You can also place images manually.

### Filtering rules

- `MIN_IMAGES_PER_CLASS = 20` — species with fewer images are excluded
- Current dataset: **47 folders** → **41 kept**, **1,536 images** used
- 80/20 stratified train/test split (`random_state=42`)

> **Note:** macOS zip extracts may create a duplicate `Data/__MACOSX/` tree. Training uses only `Data/Data/Mosquito Images/`, not `__MACOSX`.

---

## Training

### Option A — Jupyter notebook (recommended)

```bash
jupyter notebook Mos.ipynb
```

Run in order:

1. **Cell 1** — download / verify data, filter classes  
2. **Cell 5** — train/test split  
3. **Cell 10** — 5-fold CV + hyperparameter search (`FORCE_RERUN_CV = True` to retrain)  
4. **Cell 12** — final training + test evaluation  

### Option B — Background notebook execution

```bash
nohup jupyter nbconvert --to notebook --execute Mos.ipynb \
  --output Mos_executed.ipynb \
  --ExecutePreprocessor.timeout=-1 \
  > logs/mos_notebook_run.log 2>&1 &
```

Monitor:

```bash
tail -f logs/mos_notebook_run.log
pgrep -af "jupyter-nbconvert.*Mos.ipynb"
```

### Option C — Final training only (CV already done)

```bash
python run_final_training.py
```

Requires `results_class_weight/cv/cv_best_params.json` from a completed CV run.

### Training source files

| File | Purpose |
|------|---------|
| `Mos.ipynb` | End-to-end notebook |
| `cv_final_training_class_weight_cell.py` | Copy-paste CV + final training cells |
| `run_final_training.py` | Standalone final training script |

### Outputs

```
results_class_weight/
├── cv/
│   ├── cv_best_params.json
│   ├── cv_metrics.json
│   ├── cv_metrics_report.md
│   └── cv_hyperparam_search.csv
└── final/
    ├── mosquito_convnextv2_tiny_final.pth
    ├── test_metrics.json
    └── test_metrics_report.md
```

---

## Hybrid method (`v2_enhanced_memsafe`)

Combines techniques for **imbalanced fine-grained** classification:

| Component | Setting |
|-----------|---------|
| Backbone | `convnextv2_tiny` (timm, ImageNet pretrained) |
| Input size | 288 × 288 |
| Class weights | **sqrt-balanced**: \( w_c = \sqrt{N / (K \cdot n_c)} \), mean-normalized |
| Loss | **Focal loss** (γ=2) + label smoothing (0.1) |
| Augmentation | RandomResizedCrop, RandAugment, horizontal flip |
| MixUp | α = 0.3 (training only) |
| Optimizer | AdamW + cosine LR + 2-epoch warmup |
| Regularization | weight decay, drop path 0.1, grad clip 1.0 |
| CV selection | Best mean **accuracy** (tie-break: F1 macro) |
| Inference | Resize → center crop → **TTA** (avg with horizontal flip) |

### Why “hybrid”?

- **sqrt-balanced weights** — helps rare species without over-penalizing common ones (vs full `N/(K·n_c)` balancing)
- **Focal loss** — focuses on hard misclassified pairs
- **Modern augmentation + MixUp** — critical for ~30 images/class average
- **TTA** — free boost at inference

### Hyperparameter grid (12 trials)

| Parameter | Values |
|-----------|--------|
| `learning_rate` | 3e-5, 5e-5, 1e-4 |
| `batch_size` | 8, 16 |
| `weight_decay` | 0.01, 0.05 |

5-fold CV per trial; best epoch per fold = highest val accuracy; final epochs = median across folds.

---

## Project structure

```
mosquitos/
├── Mos.ipynb                          # Main notebook
├── cv_final_training_class_weight_cell.py
├── run_final_training.py
├── README.md
│
├── Data/                              # Species images (not in git — see .gitignore)
│
├── results_class_weight/              # Production model & metrics
│   ├── cv/
│   └── final/
│
├── results_without_class_weight/      # Baseline comparison
│
├── logs/
│
└── webapp/                            # MosquitoScope Flask app
    ├── app.py
    ├── model_service.py
    ├── mosquito_facts.py
    ├── disease_info.py
    ├── config.py
    ├── requirements.txt
    ├── templates/index.html
    └── static/
```

---

## Web app configuration

`webapp/config.py` points to the hybrid model:

```python
MODEL_PATH = PROJECT_ROOT / "results_class_weight/final/mosquito_convnextv2_tiny_final.pth"
TEST_METRICS_PATH = PROJECT_ROOT / "results_class_weight/final/test_metrics.json"
```

Inference matches training: **328px resize → 288 center crop**, ImageNet normalize, **TTA**.

---

## API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/health` | GET | Model status, device, class count |
| `/api/predict` | POST | Image upload → predictions + species facts |
| `/api/classes` | GET | List of 41 class names |
| `/api/diseases` | GET | Disease reference data |
| `/api/diseases/<slug>` | GET | Single disease detail |

---

## Requirements

### Training

```
torch>=2.0
torchvision>=0.15
timm>=0.9
scikit-learn
Pillow
matplotlib
gdown
jupyter
nbconvert
```

### Web app only

```
flask>=3.0
torch>=2.0
torchvision>=0.15
timm>=0.9
Pillow>=10.0
```

---

## Reproducibility

| Setting | Value |
|---------|-------|
| Random seed | 42 |
| Train/test split | 80/20 stratified, `random_state=42` |
| CV folds | 5, stratified, `random_state=42` |
| Recipe ID | `v2_enhanced_memsafe` |

Set `FORCE_RERUN_CV = False` in the CV cell to load existing results from `results_class_weight/cv/`. Set `True` after dataset changes.

---

## Publishing to GitHub

**Yes — include the `webapp/` folder.** It is source code and belongs in the repository alongside the training pipeline.

### What to upload

| Include | Why |
|---------|-----|
| `webapp/` (all `.py`, HTML, CSS, JS) | Small source files; others can run the demo |
| `Mos.ipynb`, `cv_final_training_class_weight_cell.py`, `run_final_training.py` | Training pipeline |
| `README.md`, `.gitignore` | Documentation and ignore rules |
| `results_class_weight/cv/*.json`, `*.md`, `*.csv` | CV metrics and reports (small) |
| `results_class_weight/final/test_metrics.json`, `test_metrics_report.md` | Test evaluation (no large binaries) |
| `sample_mosquitoes.png`, `augmentation_preview*.png` | Optional visuals for the README |

### What not to upload

These are listed in `.gitignore` and should stay out of normal git commits:

| Exclude | Why |
|---------|-----|
| `Data/` | Large; may have licensing or sharing restrictions |
| `*.pth` model checkpoints (~107 MB) | Too large for standard Git |
| `logs/`, `__MACOSX/` | Generated files / macOS zip artifacts |
| `Mos_executed.ipynb` | Optional — large notebook with embedded outputs |

### How to share the trained model

The webapp expects the checkpoint at:

```
results_class_weight/final/mosquito_convnextv2_tiny_final.pth
```

Choose one of these for collaborators:

1. **GitHub Release** — attach the `.pth` file to a release (recommended)
2. **Google Drive** — add a download link in this README (same approach as the dataset)
3. **Git LFS** — if you want the model tracked inside the repository

### After cloning (for users)

```bash
git clone <your-repo-url>
cd mosquitos

# 1. Download or train the model → results_class_weight/final/mosquito_convnextv2_tiny_final.pth
# 2. Download dataset → Data/ (see Dataset setup above)

pip install -r webapp/requirements.txt
cd webapp
python app.py
# → http://localhost:7860
```

Replace `<your-repo-url>` with your actual GitHub repository URL before publishing.

---

## Limitations

- **74% test accuracy** on 41 fine-grained species — strong for the dataset size but below 80% without more data
- Similar species (*Culex*, *Psorophora*, *Aedes* spp.) remain easily confused
- Single stratified split — no external geographic/temporal validation set
- Model file (~107 MB) and `Data/` are gitignored — download or train locally

---

## Citation & references

If you use this work, please cite the methods below:

- **Focal Loss:** Lin, T.-Y., et al. "Focal Loss for Dense Object Detection." ICCV 2017.
- **MixUp:** Zhang, H., et al. "mixup: Beyond Empirical Risk Minimization." ICLR 2018.
- **RandAugment:** Cubuk, E. D., et al. CVPR 2020.
- **ConvNeXt V2:** Woo, S., et al. CVPR 2023.
- **Class-balanced loss:** Cui, Y., et al. CVPR 2019.

---

## License

Add your license here (e.g. MIT). Model weights and mosquito images may have separate usage terms from the original data source.

---

## Authors

UNT Mosquito Classification Project — hybrid training pipeline and MosquitoScope web demo.

*Last updated: June 2026 — 1,536 images, 41 classes, 74.0% test accuracy (TTA).*
