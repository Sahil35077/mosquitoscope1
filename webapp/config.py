import os
from pathlib import Path

WEBAPP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEBAPP_DIR.parent


def _resolve_model_path() -> Path:
    if os.environ.get("MODEL_PATH"):
        return Path(os.environ["MODEL_PATH"])
    data_model = WEBAPP_DIR / "data" / "mosquito_convnextv2_tiny_final.pth"
    local_model = (
        PROJECT_ROOT / "results_class_weight" / "final" / "mosquito_convnextv2_tiny_final.pth"
    )
    if data_model.exists():
        return data_model
    if local_model.exists():
        return local_model
    return data_model


def _resolve_metrics_path() -> Path:
    if os.environ.get("TEST_METRICS_PATH"):
        return Path(os.environ["TEST_METRICS_PATH"])
    bundled = WEBAPP_DIR / "assets" / "test_metrics.json"
    local = PROJECT_ROOT / "results_class_weight" / "final" / "test_metrics.json"
    if bundled.exists():
        return bundled
    return local


MODEL_PATH = _resolve_model_path()
TEST_METRICS_PATH = _resolve_metrics_path()
CV_BEST_PARAMS_PATH = PROJECT_ROOT / "results_class_weight" / "cv" / "cv_best_params.json"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
MAX_UPLOAD_MB = 16
TOP_K = 5

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

PORT = int(os.environ.get("PORT", "7860"))
