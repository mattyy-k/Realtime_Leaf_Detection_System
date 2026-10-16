"""OpenCV/NumPy feature extraction for the experimental leaf classifier."""

from __future__ import annotations

import cv2
import numpy as np


RADIAL_BINS = 36
FEATURE_NAMES = [
    "aspect_ratio",
    "area_ratio",
    "perimeter_ratio",
    "circularity",
    "solidity",
    *[f"radial_{index:02d}" for index in range(RADIAL_BINS)],
]


def _decode_image(image_bytes: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError("The uploaded crop is not a readable image.")
    return image


def _leaf_contour(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    saturation_mask = cv2.inRange(hsv, np.array([20, 25, 20]), np.array([100, 255, 255]))
    _, otsu_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = cv2.bitwise_or(saturation_mask, otsu_mask)
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError("Leaf segmentation found no contour.")
    contour = max(contours, key=cv2.contourArea)
    image_area = image.shape[0] * image.shape[1]
    if cv2.contourArea(contour) < max(25.0, image_area * 0.01):
        raise ValueError("Leaf segmentation produced an unusably small contour.")
    return contour


def _radial_signature(contour: np.ndarray, centroid: tuple[float, float]) -> np.ndarray:
    points = contour.reshape(-1, 2).astype(np.float32)
    offsets = points - np.asarray(centroid, dtype=np.float32)
    angles = (np.arctan2(offsets[:, 1], offsets[:, 0]) + 2 * np.pi) % (2 * np.pi)
    distances = np.linalg.norm(offsets, axis=1)
    signature = np.zeros(RADIAL_BINS, dtype=np.float32)
    for index in range(RADIAL_BINS):
        start = index * 2 * np.pi / RADIAL_BINS
        end = (index + 1) * 2 * np.pi / RADIAL_BINS
        values = distances[(angles >= start) & (angles < end)]
        if values.size:
            signature[index] = values.max()
    if not np.any(signature):
        raise ValueError("Leaf contour did not produce a radial signature.")
    return signature / signature.max()


def extract_features(image_bytes: bytes) -> np.ndarray:
    """Return one fixed-length, scale-normalized feature vector for a leaf crop."""
    image = _decode_image(image_bytes)
    contour = _leaf_contour(image)
    height, width = image.shape[:2]
    image_area = float(height * width)
    area = float(cv2.contourArea(contour))
    perimeter = float(cv2.arcLength(contour, True))
    _, _, box_width, box_height = cv2.boundingRect(contour)
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        raise ValueError("Leaf contour has no measurable centroid.")
    centroid = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
    hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
    if hull_area == 0 or perimeter == 0:
        raise ValueError("Leaf contour has invalid area or perimeter.")

    aspect_ratio = box_width / max(box_height, 1)
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    solidity = area / hull_area
    radial = _radial_signature(contour, centroid)
    geometric = np.array(
        [aspect_ratio, area / image_area, perimeter / (2 * (width + height)),
         circularity, solidity],
        dtype=np.float32,
    )
    return np.concatenate((geometric, radial)).astype(np.float32)


def feature_names() -> list[str]:
    return list(FEATURE_NAMES)
