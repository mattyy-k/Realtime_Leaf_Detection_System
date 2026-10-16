"""Persisted lightweight classifier built on handcrafted leaf shape features."""

from __future__ import annotations

import logging
import os
import pickle
import time
from pathlib import Path

from .classical_features import extract_features

logger = logging.getLogger(__name__)
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "classical_leaf_classifier.pkl"


class ClassicalLeafClassifier:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or os.getenv("CLASSICAL_MODEL_PATH", DEFAULT_MODEL_PATH))
        self.model = None
        self.species_labels: list[str] = []
        if self.model_path.exists():
            with self.model_path.open("rb") as model_file:
                checkpoint = pickle.load(model_file)
            self.model = checkpoint["model"]
            self.species_labels = list(checkpoint["classes"])
            logger.info("Loaded classical classifier with %d classes.", len(self.species_labels))

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def classify(self, image_bytes: bytes) -> dict:
        if not self.is_available:
            raise RuntimeError(f"Classical model is not trained: {self.model_path}")
        started = time.perf_counter()
        features = extract_features(image_bytes)
        predicted_index = int(self.model.predict([features])[0])
        confidence = None
        if hasattr(self.model, "predict_proba"):
            confidence = float(max(self.model.predict_proba([features])[0])) * 100
        return {
            "species": self.species_labels[predicted_index],
            "confidence": round(confidence, 2) if confidence is not None else None,
            "inference_ms": round((time.perf_counter() - started) * 1000, 3),
            "feature_count": len(features),
        }
