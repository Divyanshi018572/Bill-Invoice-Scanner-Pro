import os
import json
import sqlite3
import time
from ocr import OCRScanner
from extractor import parse_invoice
import database
import re

def clean_amount(val):
    if not val: return 0.0
    val_str = str(val)
    m = re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', val_str)
    if m:
        return float(m.group(0).replace(',', ''))
    return 0.0

def benchmark_sroie(limit=1000):
    """
    SROIE Benchmark Suite - Production Scale.
    
    1. Processes images via OCRScanner.
    2. Parses fields via invoice_parser.
    3. Compares against Ground Truth JSONs.
    4. Persists results to invoices.db.
    """
    database.init_db()
    scanner = OCRScanner()
    
    # Correct relative paths from bill_scanner/
    img_dir = "../SROIE_Dataset/data/img/"
    key_dir = "../SROIE_Dataset/data/key/"
    
    if not os.path.exists(img_dir):
        print(f"Error: Dataset directory {img_dir} not found.")
        return

    images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if limit:
        images = images[:limit]
        
    print(f"--- Starting SROIE Production Benchmark: {len(images)} images ---")
    
    stats = {
        "processed": 0,
        "total_match": 0,
        "date_match": 0,
        "errors": 0
    }
    
    start_time = time.time()
    
    for i, img_name in enumerate(images):
        img_path = os.path.normpath(os.path.join(img_dir, img_name))
        key_name = img_name.rsplit('.', 1)[0] + '.json'
        key_path = os.path.normpath(os.path.join(key_dir, key_name))
        
        if not os.path.exists(key_path):
            continue
            
        try:
            # 1. OCR + Extraction
            raw_text = scanner.extract_text(img_path)
            parsed = parse_invoice(raw_text)
            
            # Add filename for tracking
            parsed["file_name"] = img_name
            
            # 2. Ground Truth Comparison
            with open(key_path, 'r', encoding='utf-8') as f:
                gt = json.load(f)
            
            # Extract values for accuracy comparison
            p_total = clean_amount(parsed.get('total'))
            gt_total = clean_amount(gt.get('total'))
            
            p_date = str(parsed.get('date', '') or '').strip()
            gt_date = str(gt.get('date', '') or '').strip()
            
            # Simple fuzzy matching for benchmark
            is_t_match = abs(p_total - gt_total) < 0.01 if gt_total > 0 else (p_total == gt_total)
            is_d_match = (gt_date in p_date or p_date in gt_date) if gt_date else True
            
            if is_t_match: stats["total_match"] += 1
            if is_d_match: stats["date_match"] += 1
            stats["processed"] += 1
            
            # 3. Persistent DB Save
            database.save_invoice(parsed)
            
            if (i + 1) % 10 == 0 or (i + 1) == len(images):
                elapsed = time.time() - start_time
                t_acc = (stats["total_match"] / stats["processed"]) * 100
                d_acc = (stats["date_match"] / stats["processed"]) * 100
                print(f"Prog: {i+1}/{len(images)} | Total Acc: {t_acc:.1f}% | Date Acc: {d_acc:.1f}% | Time: {elapsed:.1f}s")
                
        except Exception as e:
            stats["errors"] += 1
            print(f"Error on {img_name}: {e}")
            
    total_elapsed = time.time() - start_time
    print("\n" + "="*50)
    print(f"BENCHMARK COMPLETE")
    print(f"Processed: {stats['processed']} | Errors: {stats['errors']}")
    print(f"Final Total Accuracy: {(stats['total_match']/max(1, stats['processed'])):.2%}")
    print(f"Final Date Accuracy:  {(stats['date_match']/max(1, stats['processed'])):.2%}")
    print(f"Total Time: {total_elapsed:.1f} seconds")
    print("="*50)

if __name__ == "__main__":
    benchmark_sroie(limit=1000)
