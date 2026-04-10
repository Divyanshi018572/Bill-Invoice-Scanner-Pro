"""
benchmark.py — Accuracy evaluation script for the Bill/Invoice Scanner.

This script processes the 1,000-receipt SROIE dataset and compares
extracted fields (Vendor, Date, Total) against the ground-truth JSON files.

Usage:
    conda run -n dl_projects python benchmark.py

Metrics:
    - Vendor Accuracy: Case-normalized partial match.
    - Date Accuracy: String equality after normalization.
    - Total Accuracy: Fuzzy float equality (within 0.01).
"""

import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import torch

# Project modules
import utils
import ocr
import extractor

# Dataset paths
DATA_DIR = Path("SROIE_Dataset/data")
IMG_DIR = DATA_DIR / "img"
KEY_DIR = DATA_DIR / "key"

def normalize_text(text: str | None) -> str:
    """Normalize text for comparison (lower case, stripped, no extra whitespace)."""
    if text is None:
        return ""
    return " ".join(text.lower().strip().split())

def compare_totals(val1: float | None, val2: str | None) -> bool:
    """Compare a float (extracted) with a string (ground truth) fuzzy-style."""
    if val1 is None or val2 is None:
        return False
    try:
        # Convert val2 to float
        gt_val = float(val2.replace(",", ""))
        return abs(val1 - gt_val) < 0.01
    except ValueError:
        return False

def run_benchmark(limit: int = 1000):
    """
    Run benchmarking on the SROIE dataset images.
    
    Args:
        limit (int): Max number of images to process.
    """
    if not IMG_DIR.exists():
        print(f"ERROR: Image directory not found at {IMG_DIR}")
        return

    # Get list of images
    image_files = sorted(list(IMG_DIR.glob("*.jpg")))[:limit]
    total_images = len(image_files)
    
    results = []
    
    print(f"🚀 Starting benchmark on {total_images} images...")
    print(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

    for img_path in tqdm(image_files, desc="Benchmarking"):
        # 1. Load Ground Truth
        base_name = img_path.stem
        key_path = KEY_DIR / f"{base_name}.json"
        
        if not key_path.exists():
            continue
            
        with open(key_path, "r") as f:
            gt = json.load(f)
            
        # 2. Run Pipeline
        try:
            # Preprocess
            bgr_img = utils.preprocess_image(img_path)
            # OCR
            full_text = ocr.extract_text(bgr_img)
            # Extract fields
            extracted = extractor.parse_invoice(full_text)
            
            # 3. Compare Fields
            v_match = normalize_text(gt.get("company")) in normalize_text(extracted.get("vendor")) or \
                      normalize_text(extracted.get("vendor")) in normalize_text(gt.get("company"))
            
            d_match = normalize_text(gt.get("date")) == normalize_text(extracted.get("date"))
            
            t_match = compare_totals(extracted.get("total"), gt.get("total"))
            
            results.append({
                "file": base_name,
                "vendor_ok": v_match,
                "date_ok": d_match,
                "total_ok": t_match,
                "extracted_vendor": extracted.get("vendor"),
                "gt_vendor": gt.get("company"),
                "extracted_date": extracted.get("date"),
                "gt_date": gt.get("date"),
                "extracted_total": extracted.get("total"),
                "gt_total": gt.get("total"),
            })
            
        except Exception as e:
            print(f"ERR processing {base_name}: {e}")
            continue

    # Generate Report
    if not results:
        print("No results to report.")
        return

    df = pd.DataFrame(results)
    
    vendor_acc = df["vendor_ok"].mean() * 100
    date_acc = df["date_ok"].mean() * 100
    total_acc = df["total_ok"].mean() * 100
    
    print("\n" + "="*40)
    print("      SROIE BENCHMARK REPORT      ")
    print("="*40)
    print(f"Total Processed: {len(df)}")
    print(f"Vendor Accuracy:  {vendor_acc:5.1f}%")
    print(f"Date Accuracy:    {date_acc:5.1f}%")
    print(f"Total Accuracy:   {total_acc:5.1f}%")
    print("="*40)

    # Save mismatches for analysis
    mismatches = df[(~df["vendor_ok"]) | (~df["date_ok"]) | (~df["total_ok"])]
    mismatches.to_csv("benchmark_mismatches.csv", index=False)
    print(f"Mismatches saved to 'benchmark_mismatches.csv' ({len(mismatches)} rows)")

if __name__ == "__main__":
    run_benchmark()
