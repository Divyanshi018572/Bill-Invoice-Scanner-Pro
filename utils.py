"""
utils.py — Image preprocessing utilities for the Bill/Invoice Scanner.

Responsibilities:
- preprocess_image(): denoise, deskew, and threshold a bill image for OCR
- pil_to_cv2(): convert a PIL Image to a BGR numpy array for OpenCV/PaddleOCR

These are pure functions with no side effects.
"""

from pathlib import Path
import numpy as np
import cv2
from PIL import Image


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """
    Convert a PIL Image to a cv2-compatible BGR numpy array.

    PaddleOCR expects BGR format (OpenCV convention). PIL images are
    RGB by default — passing RGB to PaddleOCR inverts colors and
    degrades OCR quality significantly. This function corrects that.

    Args:
        pil_image: A PIL Image object in any mode (RGB, RGBA, L, etc.)

    Returns:
        A numpy array of dtype uint8 in BGR channel order.
    """
    # Ensure we are working in RGB first (handles RGBA, L, P, etc.)
    pil_rgb = pil_image.convert("RGB")
    # Convert to numpy array (H, W, 3) in RGB
    rgb_array = np.array(pil_rgb, dtype=np.uint8)
    # Flip RGB → BGR (OpenCV/PaddleOCR format)
    bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    return bgr_array


def _deskew(gray: np.ndarray) -> np.ndarray:
    """
    Detect and correct the skew angle of a grayscale image.

    Uses contour analysis via minAreaRect to find the dominant angle.
    Guards against the -45° quadrant-ambiguity by skipping rotation
    when the absolute angle is less than 1 degree (straight images do
    not need correction and would be mis-rotated otherwise).

    Args:
        gray: A 2D uint8 numpy array (grayscale image).

    Returns:
        The deskewed grayscale image as a uint8 numpy array.
    """
    # Threshold to binary for contour detection
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))

    if coords.shape[0] == 0:
        # No content found — return original unchanged
        return gray

    angle = cv2.minAreaRect(coords)[-1]

    # Resolve quadrant ambiguity: minAreaRect returns angles in [-90, 0)
    if angle < -45:
        angle = 90 + angle  # e.g. -80° → 10°

    # Failure-mode fix: skip rotation for near-zero angles
    if abs(angle) < 1.0:
        return gray

    (h, w) = gray.shape
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        gray,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return deskewed


def preprocess_image(image_path: str | Path) -> np.ndarray:
    """
    Load and preprocess a bill image for OCR.

    Pipeline:
        1. Load and convert to grayscale
        2. Denoise (remove camera grain and paper texture)
        3. Deskew (correct slight rotation from camera angle)
        4. Adaptive threshold (handle uneven lighting / shadows)
        5. Convert result to BGR (PaddleOCR expected format)

    Args:
        image_path: Path to the image file (str or pathlib.Path).

    Returns:
        A preprocessed numpy array of dtype uint8 in BGR format,
        ready to be passed directly to PaddleOCR.

    Raises:
        FileNotFoundError: If the image path does not exist.
        ValueError: If the file cannot be decoded as an image.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # Step 1 — Load as BGR using OpenCV (already BGR, no conversion needed)
    bgr = cv2.imread(str(path))
    if bgr is None:
        raise ValueError(f"Could not decode image: {path}")

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Step 2 — Denoise: remove grain while preserving text edges
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # Step 3 — Deskew
    deskewed = _deskew(denoised)

    # Step 4 — Adaptive threshold: pure black/white; robust to uneven lighting
    binary = cv2.adaptiveThreshold(
        deskewed,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )

    # Step 5 — Convert grayscale binary back to BGR for PaddleOCR
    bgr_output = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    return bgr_output
