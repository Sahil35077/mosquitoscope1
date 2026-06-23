"""Upload the trained checkpoint to Hugging Face Hub (public model repo)."""

import argparse
import json
import sys
from pathlib import Path

from huggingface_hub import HfApi, create_repo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "results_class_weight" / "final" / "mosquito_convnextv2_tiny_final.pth"
DEFAULT_METRICS = ROOT / "results_class_weight" / "final" / "test_metrics.json"
MODEL_FILENAME = "mosquito_convnextv2_tiny_final.pth"


def build_model_card(metrics_path: Path) -> str:
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    acc = metrics.get("test_accuracy_tta") or metrics.get("test_accuracy")
    cv = metrics.get("cv_mean_accuracy")
    acc_pct = f"{acc * 100:.1f}%" if acc else "N/A"
    cv_pct = f"{cv * 100:.1f}%" if cv else "N/A"

    return f"""---
license: mit
tags:
  - image-classification
  - mosquitoes
  - convnext
  - fine-grained-classification
library_name: timm
---

# MosquitoScope — ConvNeXt V2 Tiny (41 classes)

Production checkpoint for the [MosquitoScope](https://github.com) web demo: 41 mosquito species, hybrid class-weighted training (`v2_enhanced_memsafe`).

## Metrics

| Metric | Value |
|--------|-------|
| Test accuracy (TTA) | {acc_pct} |
| CV mean accuracy | {cv_pct} |
| Architecture | convnextv2_tiny @ 288px |
| Classes | 41 |
| Train / test | {metrics.get('train_samples', '?')} / {metrics.get('test_samples', '?')} |

## Usage

```python
import torch
import timm

checkpoint = torch.load("{MODEL_FILENAME}", map_location="cpu", weights_only=False)
model = timm.create_model(checkpoint["model_name"], pretrained=False, num_classes=len(checkpoint["classes"]))
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()
```

Bundled with the MosquitoScope Flask app; Render pulls this file at deploy time via `HF_MODEL_REPO`.
"""


def upload(repo_id: str, model_path: Path, metrics_path: Path, private: bool = False) -> str:
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    api = HfApi()
    create_repo(repo_id, repo_type="model", exist_ok=True, private=private)

    card_path = ROOT / "scripts" / ".hf_readme_upload.md"
    card_path.write_text(build_model_card(metrics_path))

    print(f"Uploading {model_path.name} ({model_path.stat().st_size // 1_048_576} MB) to {repo_id}...")
    api.upload_file(
        path_or_fileobj=str(model_path),
        path_in_repo=MODEL_FILENAME,
        repo_id=repo_id,
        repo_type="model",
    )
    api.upload_file(
        path_or_fileobj=str(metrics_path) if metrics_path.exists() else "{}",
        path_in_repo="test_metrics.json",
        repo_id=repo_id,
        repo_type="model",
    )
    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    card_path.unlink(missing_ok=True)

    url = f"https://huggingface.co/{repo_id}"
    resolve_url = f"https://huggingface.co/{repo_id}/resolve/main/{MODEL_FILENAME}"
    print(f"\nDone! Model repo: {url}")
    print(f"Direct file URL: {resolve_url}")
    print(f"\nSet on Render: HF_MODEL_REPO={repo_id}")
    return repo_id


def main():
    parser = argparse.ArgumentParser(description="Upload MosquitoScope checkpoint to Hugging Face Hub")
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face model repo, e.g. yourusername/mosquitoscope-convnextv2-tiny",
    )
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    try:
        upload(args.repo_id, args.model_path, args.metrics_path, private=args.private)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("\nLog in first:  huggingface-cli login", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
