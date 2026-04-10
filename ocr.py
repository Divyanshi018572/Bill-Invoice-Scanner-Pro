"""
ocr.py — Optimized EasyOCR wrapper for Bill/Invoice Scanner.
Enabled for GPU acceleration on NVIDIA GTX 1650.
Part of the production-grade bill_scanner package.
"""

import logging
import easyocr
import os

# Suppress verbose easyocr/torch logs
# os.environ["OMP_NUM_THREADS"] = "1" # Optional CPU threading optimization
logging.getLogger("easyocr").setLevel(logging.ERROR)

_reader_instance = None

def _get_reader():
    global _reader_instance
    if _reader_instance is None:
        # Initializing EasyOCR Reader with GPU=True for production scale-up
        try:
            _reader_instance = easyocr.Reader(['en'], gpu=True)
            print("INFO: EasyOCR initialized with GPU acceleration.")
        except Exception as e:
            print(f"WARNING: GPU initialization failed, falling back to CPU. Error: {e}")
            _reader_instance = easyocr.Reader(['en'], gpu=False)
    return _reader_instance

class OCRScanner:
    def extract_text(self, image_path):
        """
        Extends the OCR functionality using EasyOCR with GPU acceleration.
        Returns extracted text as a newline-joined string.
        """
        try:
            reader = _get_reader()
            # readtext returns List[Tuple(bbox, text, confidence)]
            results = reader.readtext(image_path)
            
            if not results:
                return ""
            
            # Simple top-to-bottom text joining
            texts = [res[1] for res in results]
            return "\n".join(texts)
        except Exception as e:
            print(f"EasyOCR Error during extraction: {e}")
            return ""
