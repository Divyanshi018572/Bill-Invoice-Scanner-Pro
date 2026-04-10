"""
test_pipeline.py - ASCII Sanitized Validation.

Demonstrates Phase 1 & 2 success criteria from bill_invoice_scanner.md.
"""

import os
import sys
from pathlib import Path

# Fix terminal encoding issues on Windows
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(str(Path(__file__).parent))

import utils
import ocr
import extractor
import database

def validate_pipeline(sample_count=5):
    print(f"--- Starting Validation of {sample_count} Dataset Samples ---")
    
    images_dir = Path(__file__).parent / "test_images"
    image_files = sorted(list(images_dir.glob("*.jpg")))[:sample_count]
    
    if not image_files:
        print("Error: No images found in bill_scanner/test_images/.")
        return

    success_count = 0
    
    for img_path in image_files:
        print(f"\nProcessing: {img_path.name}...")
        
        try:
            bgr_preprocessed = utils.preprocess_image(str(img_path))
            full_text = ocr.extract_text(bgr_preprocessed)
            
            # Phase 2: Field Extraction
            parsed = extractor.parse_invoice(full_text)
            total = parsed.get("total")
            vendor = parsed.get("vendor")
            
            if total is not None:
                # ASCII-only output
                print(f"OK: Found Total: {total} | Vendor: {vendor}")
                success_count += 1
            else:
                print(f"FAIL: Total not found for {img_path.name}")
                print(f"Parsed fields for debug: {parsed}")

        except Exception as e:
            print(f"ERROR processing {img_path.name}: {e}")

    print("\n" + "=" * 40)
    print(f"FINAL RESULT: {success_count}/{sample_count} bills successfully parsed.")
    print("Success Criterion (Total Amount must always be found):", "PASSED" if success_count == sample_count else "FAILED")
    print("=" * 40)

if __name__ == "__main__":
    database.init_db()
    validate_pipeline(5)
