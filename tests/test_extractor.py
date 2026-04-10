"""
test_extractor.py — Assert-based tests for extractor.py using hardcoded OCR strings.

Run with: pytest test_extractor.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractor import (
    extract_vendor,
    extract_date,
    extract_invoice_number,
    extract_amounts,
    parse_invoice,
)

# ---------------------------------------------------------------------------
# Realistic OCR output strings simulating real bill scans
# ---------------------------------------------------------------------------

SAMPLE_BILL_1 = """TAX INVOICE
SuperMart Inc.
123 Main St, Springfield
Date: 15/01/2024
Invoice No. INV-2024-001
Apples $4.50
Bread $2.00
Milk $3.50
Subtotal: $10.00
GST (5%): $0.50
Total: $10.50"""

SAMPLE_BILL_2 = """RESTAURANT BILL
Joe's Diner
Date: 22-Feb-2024
INV# 99824
Burger 15.00
Fries 5.00
Cola 3.00
Sub Total: 23.00
Tax: 2.00
TOTAL: $25.00"""

SAMPLE_BILL_3 = """TECH GADGETS LLC
Invoice No: TECH-882
Date: 05 Mar 2024
Mouse Rs.1,250
Keyboard Rs.2,500
Subtotal Rs.3,500
GST 10% Rs.350
Total : ₹3,850"""


# ---------------------------------------------------------------------------
# Test 1: extract_vendor skips 'TAX INVOICE' header and returns company name
# ---------------------------------------------------------------------------
def test_extract_vendor_skips_header():
    """Vendor extraction must skip generic headers and return first real company name."""
    vendor = extract_vendor(SAMPLE_BILL_1)
    assert vendor is not None, "Vendor must not be None"
    assert "SuperMart" in vendor, f"Expected 'SuperMart' in vendor, got: {vendor}"
    print(f"PASS: test_extract_vendor_skips_header → {vendor}")


# ---------------------------------------------------------------------------
# Test 2: extract_date handles multiple formats
# ---------------------------------------------------------------------------
def test_extract_date_multiple_formats():
    """Date extractor must handle DD/MM/YYYY, DD-Mon-YYYY, and DD Mon YYYY."""
    date1 = extract_date(SAMPLE_BILL_1)
    assert date1 is not None and "2024" in date1, f"Bill 1 date failed: {date1}"

    date2 = extract_date(SAMPLE_BILL_2)
    assert date2 is not None, f"Bill 2 date (DD-Mon-YYYY) failed: {date2}"

    date3 = extract_date(SAMPLE_BILL_3)
    assert date3 is not None and "Mar" in date3 or (date3 and "2024" in date3), \
        f"Bill 3 date (DD Mon YYYY) failed: {date3}"

    print(f"PASS: test_extract_date_multiple_formats → {date1} | {date2} | {date3}")


# ---------------------------------------------------------------------------
# Test 3: extract_invoice_number returns correct reference
# ---------------------------------------------------------------------------
def test_extract_invoice_number():
    """Invoice number extractor must identify INV-XXXX and TECH-XXX patterns."""
    inv1 = extract_invoice_number(SAMPLE_BILL_1)
    assert inv1 is not None, "Invoice number must not be None for bill 1"
    assert "INV-2024-001" in inv1, f"Expected INV-2024-001, got: {inv1}"

    inv3 = extract_invoice_number(SAMPLE_BILL_3)
    assert inv3 is not None, "Invoice number must not be None for bill 3"
    assert "TECH-882" in inv3, f"Expected TECH-882, got: {inv3}"

    print(f"PASS: test_extract_invoice_number → {inv1} | {inv3}")


# ---------------------------------------------------------------------------
# Test 4: extract_amounts correctly extracts total (case-insensitive, with space before colon)
# ---------------------------------------------------------------------------
def test_extract_amounts_total():
    """Total must be extracted case-insensitively and with space before colon."""
    amounts1 = extract_amounts(SAMPLE_BILL_1)
    assert amounts1["total"] == 10.50, f"Bill 1 total: expected 10.50, got {amounts1['total']}"

    amounts2 = extract_amounts(SAMPLE_BILL_2)
    assert amounts2["total"] == 25.00, f"Bill 2 total (UPPERCASE): expected 25.00, got {amounts2['total']}"

    amounts3 = extract_amounts(SAMPLE_BILL_3)
    assert amounts3["total"] == 3850.00, f"Bill 3 total (space before colon): expected 3850.00, got {amounts3['total']}"

    print(f"PASS: test_extract_amounts_total → {amounts1['total']} | {amounts2['total']} | {amounts3['total']}")


# ---------------------------------------------------------------------------
# Test 5: parse_invoice returns complete dict with all required keys
# ---------------------------------------------------------------------------
def test_parse_invoice_returns_complete_dict():
    """parse_invoice must return dict with all required keys."""
    result = parse_invoice(SAMPLE_BILL_1)
    required_keys = {"vendor", "date", "invoice_number", "subtotal", "gst", "total", "raw_text"}
    assert required_keys == set(result.keys()), f"Missing keys: {required_keys - set(result.keys())}"
    assert result["raw_text"] == SAMPLE_BILL_1, "raw_text must be the original input"
    assert result["total"] == 10.50
    print(f"PASS: test_parse_invoice_returns_complete_dict → {result}")


if __name__ == "__main__":
    test_extract_vendor_skips_header()
    test_extract_date_multiple_formats()
    test_extract_invoice_number()
    test_extract_amounts_total()
    test_parse_invoice_returns_complete_dict()
    print("\nAll extractor tests passed!")
