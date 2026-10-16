"""Train and evaluate the experimental classical leaf classifier.

The command expects an existing split_dataset.py layout:
dataset/{train,valid,test}/{Guava,Lemon,Lychee,Mango,Olive}/*.jpg
"""

from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path

import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from services.classical_features import extract_features

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_split(dataset: Path, split: str, classes: list[str]) -> tuple[np.ndarray, np.ndarray, int]:
    features, labels, skipped = [], [], 0
    for label, class_name in enumerate(classes):
        for image_path in sorted((dataset / split / class_name).glob("*")):
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            try:
                decoded = cv2.imread(str(image_path))
                if decoded is None:
                    raise ValueError("Image could not be decoded.")
                encoded = cv2.imencode(".png", decoded)
                if not encoded[0]:
                    raise ValueError("Image could not be encoded.")
                image = encoded[1].tobytes()
                features.append(extract_features(image))
                labels.append(label)
            except (ValueError, cv2.error):
                skipped += 1
    if not features:
        raise ValueError(f"No valid images found in {dataset / split}.")
    return np.asarray(features), np.asarray(labels), skipped


def train_and_evaluate(dataset_path: str, output_path: str) -> None:
    dataset = Path(dataset_path)
    classes = sorted(path.name for path in (dataset / "train").iterdir() if path.is_dir())
    if len(classes) < 2:
        raise ValueError("Training data must contain at least two class directories.")
    splits = {split: load_split(dataset, split, classes) for split in ("train", "valid", "test")}
    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced")
    model.fit(splits["train"][0], splits["train"][1])

    print(f"Classes: {classes}")
    for split in ("train", "valid", "test"):
        started = time.perf_counter()
        predictions = model.predict(splits[split][0])
        elapsed = (time.perf_counter() - started) * 1000 / len(predictions)
        print(f"\n{split}: accuracy={accuracy_score(splits[split][1], predictions):.4f}, "
              f"mean_inference_ms={elapsed:.3f}, skipped={splits[split][2]}")
        if split == "test":
            print(classification_report(
                splits[split][1], predictions, labels=range(len(classes)),
                target_names=classes, zero_division=0,
            ))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as model_file:
        pickle.dump({"model": model, "classes": classes}, model_file)
    print(f"Saved classical model to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Dataset containing train/valid/test class folders")
    parser.add_argument("--output", default="models/classical_leaf_classifier.pkl")
    args = parser.parse_args()
    train_and_evaluate(args.dataset, args.output)
