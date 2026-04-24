"""Shared image-folder path helpers."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
IMAGE_ROOT = REPO_ROOT / "images"

PUBLIC_DATASET_SOURCES = ("FLUX", "FLUX2", "NanoBanana", "Qwen", "DALL-E", "GPTImages2")
LOCAL_REFERENCE_SOURCES = ("AdobeStock", "GoogleSearch")
LOCAL_IMAGE_SOURCES = PUBLIC_DATASET_SOURCES + LOCAL_REFERENCE_SOURCES


def resolve_image_path(path: str | Path) -> Path:
    """Resolve old source-relative paths to the new images/ layout."""
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate

    parts = candidate.parts
    if parts and parts[0] in LOCAL_IMAGE_SOURCES:
        return IMAGE_ROOT / candidate

    return candidate
