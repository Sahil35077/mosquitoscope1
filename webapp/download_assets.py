"""Download model checkpoint at build/start time (for Render / CI)."""

import os
import sys
from pathlib import Path

import requests

WEBAPP_DIR = Path(__file__).resolve().parent
DATA_DIR = WEBAPP_DIR / "data"
MODEL_FILENAME = "mosquito_convnextv2_tiny_final.pth"
MODEL_PATH = DATA_DIR / MODEL_FILENAME


def download_model(url: str, dest: Path = MODEL_PATH) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"Model already present: {dest} ({dest.stat().st_size // 1_048_576} MB)")
        return dest

    print(f"Downloading model from {url[:80]}...")
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r  {pct}% ({downloaded // 1_048_576} MB)", end="", flush=True)
    print(f"\nSaved model to {dest}")
    return dest


def download_from_huggingface(repo_id: str, dest: Path = MODEL_PATH) -> Path:
    from huggingface_hub import hf_hub_download

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"Model already present: {dest} ({dest.stat().st_size // 1_048_576} MB)")
        return dest

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    print(f"Downloading from Hugging Face: {repo_id}/{MODEL_FILENAME}")
    path = hf_hub_download(
        repo_id=repo_id,
        filename=MODEL_FILENAME,
        local_dir=str(DATA_DIR),
        local_dir_use_symlinks=False,
        token=token or None,
    )
    return Path(path)


def ensure_model() -> Path:
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 1_000_000:
        return MODEL_PATH

    local = (
        WEBAPP_DIR.parent
        / "results_class_weight"
        / "final"
        / MODEL_FILENAME
    )
    if local.exists():
        return local

    hf_repo = os.environ.get("HF_MODEL_REPO", "").strip()
    if hf_repo:
        return download_from_huggingface(hf_repo)

    url = os.environ.get("MODEL_DOWNLOAD_URL", "").strip()
    if url:
        return download_model(url)

    raise FileNotFoundError(
        "Model not found. Set HF_MODEL_REPO (e.g. username/mosquitoscope-convnextv2-tiny), "
        f"MODEL_DOWNLOAD_URL, or place the checkpoint at {MODEL_PATH}"
    )


if __name__ == "__main__":
    try:
        ensure_model()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
