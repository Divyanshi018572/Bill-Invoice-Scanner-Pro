"""
test_ocr.py — 3 assert-based tests for ocr.py using the preprocessed test images.

Run with: pytest test_ocr.py -v
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from utils import preprocess_image
from ocr import extract_text, extract_text_with_boxes


# ---------------------------------------------------------------------------
# Test 1: extract_text returns a non-empty string from a clean bill image
# ---------------------------------------------------------------------------
def test_extract_text_returns_nonempty_string():
    """extract_text must return a non-empty string for a clear bill image."""
    img = preprocess_image("test_images/bill_1_perfect.jpg")
    result = extract_text(img)
    assert isinstance(result, str), "extract_text must return a str"
    assert len(result.strip()) > 0, "extract_text must not return empty string"
    print(f"PASS: test_extract_text_returns_nonempty_string\nExtracted:\n{result}\n")


# ---------------------------------------------------------------------------
# Test 2: extracted text contains at least one digit (bills always have amounts)
# ---------------------------------------------------------------------------
def test_extracted_text_contains_digit():
    """Bills always contain numeric amounts — OCR result must have at least one digit."""
    img = preprocess_image("test_images/bill_1_perfect.jpg")
    result = extract_text(img)
    has_digit = any(ch.isdigit() for ch in result)
    assert has_digit, f"Expected at least one digit in OCR output, got:\n{result}"
    print("PASS: test_extracted_text_contains_digit")


# ---------------------------------------------------------------------------
# Test 3: extract_text_with_boxes returns list of dicts with required keys
# ---------------------------------------------------------------------------
def test_extract_text_with_boxes_structure():
    """extract_text_with_boxes must return list of dicts with text/box/score keys."""
    img = preprocess_image("test_images/bill_3_noisy.jpg")
    results = extract_text_with_boxes(img)
    assert isinstance(results, list), "Must return a list"
    if len(results) > 0:
        item = results[0]
        assert "text" in item, "Each item must have 'text' key"
        assert "box" in item, "Each item must have 'box' key"
        assert "score" in item, "Each item must have 'score' key"
        assert isinstance(item["score"], float), "Score must be a float"
        assert item["score"] >= 0.6, f"All scores must be >= 0.6, got {item['score']}"
    print(f"PASS: test_extract_text_with_boxes_structure ({len(results)} boxes found)")


if __name__ == "__main__":
    test_extract_text_returns_nonempty_string()
    test_extracted_text_contains_digit()
    test_extract_text_with_boxes_structure()
    print("\nAll OCR tests passed!")
