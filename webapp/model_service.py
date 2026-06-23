import json
import os
from io import BytesIO

import timm
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from webapp.config import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    MODEL_PATH,
    TEST_METRICS_PATH,
    TOP_K,
)
from webapp.download_assets import ensure_model


class MosquitoClassifier:
    def __init__(self):
        force_cpu = os.environ.get("FORCE_CPU", "").lower() in ("1", "true", "yes")
        self.device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.classes = []
        self.label_to_idx = {}
        self.idx_to_label = {}
        self.image_size = 224
        self.transform = None
        self.model_metrics = {}
        self.per_class_metrics = {}
        self._load()

    def _load(self):
        model_path = ensure_model()
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.classes = checkpoint["classes"]
        self.label_to_idx = checkpoint["label_to_idx"]
        self.idx_to_label = {int(k): v for k, v in checkpoint["idx_to_label"].items()}
        cfg = checkpoint.get("config", {})
        self.image_size = int(
            cfg.get("image_size") or checkpoint.get("image_size") or 224
        )

        self.model = timm.create_model(
            checkpoint["model_name"],
            pretrained=False,
            num_classes=len(self.classes),
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        # Match validation / test pipeline from training (resize + center crop)
        resize_side = int(self.image_size * 1.14)
        self.transform = transforms.Compose([
            transforms.Resize(resize_side),
            transforms.CenterCrop(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

        if TEST_METRICS_PATH.exists():
            with open(TEST_METRICS_PATH) as f:
                metrics = json.load(f)
            self.model_metrics = {
                "test_accuracy": metrics.get("test_accuracy"),
                "test_f1_macro": metrics.get("metrics", {}).get("f1_macro"),
                "test_f1_weighted": metrics.get("metrics", {}).get("f1_weighted"),
                "cv_mean_accuracy": metrics.get("cv_mean_accuracy"),
                "model_name": metrics.get("model_name", "convnextv2_tiny"),
                "image_size": self.image_size,
                "train_samples": metrics.get("train_samples"),
                "test_samples": metrics.get("test_samples"),
                "class_weight_method": metrics.get("class_weight_method"),
                "training_recipe": metrics.get("training_recipe"),
            }
            self.per_class_metrics = metrics.get("metrics", {}).get("per_class", {})

    def predict(self, image_bytes: bytes, top_k: int = TOP_K) -> dict:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            flipped = torch.flip(tensor, dims=[3])
            logits = (self.model(tensor) + self.model(flipped)) / 2.0
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]

        order = probs.argsort()[::-1][:top_k]
        predictions = [
            {
                "class": self.idx_to_label[int(i)],
                "confidence": float(probs[i]),
                "confidence_pct": round(float(probs[i]) * 100, 2),
            }
            for i in order
        ]

        return {
            "top_class": predictions[0]["class"],
            "top_confidence_pct": predictions[0]["confidence_pct"],
            "predictions": predictions,
            "image_size": list(image.size),
        }

    def evaluate_ground_truth(self, predicted: str, ground_truth: str) -> dict:
        correct = predicted == ground_truth
        gt_metrics = self.per_class_metrics.get(ground_truth, {})
        pred_metrics = self.per_class_metrics.get(predicted, {})
        return {
            "ground_truth": ground_truth,
            "predicted": predicted,
            "correct": correct,
            "result": "Correct" if correct else "Incorrect",
            "ground_truth_test_metrics": {
                "precision": gt_metrics.get("precision"),
                "recall": gt_metrics.get("recall"),
                "f1": gt_metrics.get("f1"),
                "support": gt_metrics.get("support"),
            },
            "predicted_class_test_metrics": {
                "precision": pred_metrics.get("precision"),
                "recall": pred_metrics.get("recall"),
                "f1": pred_metrics.get("f1"),
                "support": pred_metrics.get("support"),
            },
        }


_classifier = None


def get_classifier() -> MosquitoClassifier:
    global _classifier
    if _classifier is None:
        _classifier = MosquitoClassifier()
    return _classifier
