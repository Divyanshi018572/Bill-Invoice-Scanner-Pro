"""
test_utils.py — 3 assert-based tests for utils.py using real test images.

Run with: pytest test_utils.py -v
"""

import numpy as np
import sys
from pathlib import Path

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from utils import preprocess_image, pil_to_cv2
from PIL import Image


# ---------------------------------------------------------------------------
# Test 1: preprocess_image returns a uint8 numpy array
# ---------------------------------------------------------------------------
def test_preprocess_returns_uint8_numpy_array():
    """preprocess_image must return a numpy array with dtype uint8."""
    result = preprocess_image("test_images/bill_1_perfect.jpg")
    assert isinstance(result, np.ndarray), "Output must be a numpy array"
    assert result.dtype == np.uint8, f"Expected uint8, got {result.dtype}"
    print("PASS: test_preprocess_returns_uint8_numpy_array")


# ---------------------------------------------------------------------------
# Test 2: preprocess_image output has 3 channels (BGR)
# ---------------------------------------------------------------------------
def test_preprocess_output_is_3_channel():
    """preprocess_image must return a 3-channel (H, W, 3) array for PaddleOCR."""
    result = preprocess_image("test_images/bill_2_skewed.jpg")
    assert result.ndim == 3, f"Expected 3D array (H,W,C), got shape {result.shape}"
    assert result.shape[2] == 3, f"Expected 3 channels (BGR), got {result.shape[2]}"
    print("PASS: test_preprocess_output_is_3_channel")


# ---------------------------------------------------------------------------
# Test 3: pil_to_cv2 correctly converts a PIL image to a BGR uint8 array
# ---------------------------------------------------------------------------
def test_pil_to_cv2_returns_bgr_uint8():
    """pil_to_cv2 must return uint8 array and flip RGB channels to BGR."""
    # Create a simple RGB PIL image with a known red pixel
    pil_img = Image.new("RGB", (100, 100), color=(255, 0, 0))  # pure red in RGB
    result = pil_to_cv2(pil_img)

    assert isinstance(result, np.ndarray), "Output must be numpy array"
    assert result.dtype == np.uint8, f"Expected uint8, got {result.dtype}"
    assert result.ndim == 3 and result.shape[2] == 3, "Expected (H,W,3) array"

    # In BGR: red pixel (255,0,0) RGB becomes (0,0,255) BGR
    r_channel = result[50, 50, 2]  # BGR index 2 = Red
    b_channel = result[50, 50, 0]  # BGR index 0 = Blue
    assert r_channel == 255, f"Expected Red=255 in BGR[2], got {r_channel}"
    assert b_channel == 0, f"Expected Blue=0 in BGR[0], got {b_channel}"
    print("PASS: test_pil_to_cv2_returns_bgr_uint8")


if __name__ == "__main__":
    test_preprocess_returns_uint8_numpy_array()
    test_preprocess_output_is_3_channel()
    test_pil_to_cv2_returns_bgr_uint8()
    print("\nAll utils tests passed!")
