"""Opt-in endpoint for the experimental handcrafted-feature classifier."""

import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ClassicalClassificationResponse(BaseModel):
    species: str
    confidence: float | None
    inference_ms: float
    feature_count: int


@router.post("/classify-classical", response_model=ClassicalClassificationResponse)
def classify_classical(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are accepted.")
    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file received.")
    classifier = request.app.state.classical_classifier
    if not classifier.is_available:
        raise HTTPException(
            status_code=503,
            detail="Classical model is not trained. Run train_classical.py first.",
        )
    try:
        result = classifier.classify(image_bytes)
        logger.info("Classical classification result: %s", result)
        return result
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.error("Classical classification error: %s", error, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal classical classification error.") from error
