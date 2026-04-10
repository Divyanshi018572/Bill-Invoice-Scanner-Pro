"""
extractor.py — Regex-based field parser for the Bill/Invoice Scanner.

Responsibilities:
- extract_vendor(): find the company/vendor name from raw OCR text
- extract_date(): find the invoice date in multiple date formats
- extract_invoice_number(): find the invoice/bill reference number
- extract_amounts(): find subtotal, GST/tax, and total amounts
- parse_invoice(): master function — calls all above, returns single dict

All functions accept a raw text string and return a value or None.
No imports from other project modules — this module is self-contained.
"""

from __future__ import annotations
import re


# ---------------------------------------------------------------------------
# Compiled regex patterns (compile once at module load for performance)
# ---------------------------------------------------------------------------

# Known header strings to skip when detecting vendor name
_SKIP_HEADERS = {
    "tax invoice", "invoice", "bill", "receipt", "gst invoice",
    "retail invoice", "cash receipt", "sale receipt", "original",
    "duplicate", "restaurant bill", "restaurant", "bill of supply",
}

# Date patterns: DD/MM/YYYY · DD-MM-YYYY · DD Mon YYYY · Mon DD YYYY · DD-Mon-YYYY
_DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"),
    re.compile(
        r"\b(\d{1,2}\s+"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"\s+\d{2,4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"\s+\d{1,2},?\s+\d{2,4}\b",
        re.IGNORECASE,
    ),
    # DD-Mon-YYYY e.g. 22-Feb-2024
    re.compile(
        r"\b(\d{1,2}[-/]"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"[-/]\d{2,4})\b",
        re.IGNORECASE,
    ),
]

# Invoice / bill number patterns
_INVOICE_NO_PATTERN = re.compile(
    r"\b(?:invoice\s*(?:no\.?|#|number|num\.?)|inv\.?\s*(?:no\.?|#)?|bill\s*(?:no\.?|#))"
    r"\s*[:\-]?\s*([A-Z0-9][-A-Z0-9/]{2,30})",
    re.IGNORECASE,
)

# Amount pattern: handles ₹ Rs. $ and comma-thousands
_AMOUNT_PATTERN = re.compile(
    r"(?:₹|Rs\.?|\$)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"
)

# Keyword matchers for each amount field (case-insensitive)
# Highly flexible to handle dots, RM, and multi-line gaps
_TOTAL_KEYWORDS = re.compile(
    r"(?:round\s*d\s*total|grand\s*total|total\s*payable|total\s*due|total\s*amount|net\s*amount|total|payable)\b"
    r"[\s\.\:\(RM\)]*?"  # Handle : (RM) .... etc
    r"([\d,]+\.\d{2})\b",
    re.IGNORECASE | re.DOTALL,
)
_SUBTOTAL_KEYWORDS = re.compile(
    r"\b(?:subtotal|sub\s*total|net\s*amount|amount\s*before\s*tax)\s*[:\-]?\s*"
    r"(?:₹|Rs\.?|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
_GST_KEYWORDS = re.compile(
    r"\b(?:gst|cgst|sgst|igst|vat|tax|service\s*tax)\s*(?:\(?\d+%?\)?)?\s*[:\-]?\s*"
    r"(?:₹|Rs\.?|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_amount(raw: str) -> float | None:
    """
    Parse a raw amount string (possibly with commas/currency symbols) to float.

    Args:
        raw: A string like '1,250.00', '1250', '₹ 1,250'.

    Returns:
        Float value, or None if parsing fails.
    """
    if raw is None:
        return None
    cleaned = raw.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def extract_vendor(text: str) -> str | None:
    """
    Extract the vendor/company name from raw OCR text.

    Strategy: the first non-empty, non-numeric line that is not a known
    generic header (e.g., 'TAX INVOICE') is usually the vendor name.

    Args:
        text: Raw OCR output as a multi-line string.

    Returns:
        Vendor name string, or None if not identifiable.
    """
    if not text:
        return None

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        lower = line.lower()
        # Skip known generic headers
        if lower in _SKIP_HEADERS:
            continue
        # Skip lines that are purely numeric or very short
        if re.fullmatch(r"[\d\s\-/.,]+", line) or len(line) < 3:
            continue
        # Skip lines that look like dates or invoice numbers
        if _DATE_PATTERNS[0].search(line) or _INVOICE_NO_PATTERN.search(line):
            continue
        return line

    return None


def extract_date(text: str) -> str | None:
    """
    Extract the invoice date from raw OCR text.

    Tries patterns in sequence: numeric (DD/MM/YYYY), then written-month
    variants. Returns the first match found.

    Args:
        text: Raw OCR output as a multi-line string.

    Returns:
        Date string as found in the text, or None if not found.
    """
    if not text:
        return None

    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1) if match.lastindex else match.group(0)

    return None


def extract_invoice_number(text: str) -> str | None:
    """
    Extract the invoice/bill reference number from raw OCR text.

    Matches common patterns: 'Invoice No.', 'INV#', 'Bill No:', etc.
    Avoids matching headers like 'TAX INVOICE' by checking line-by-line
    and ensuring the label is followed by a potential reference.

    Args:
        text: Raw OCR output as a multi-line string.

    Returns:
        Invoice number string, or None if not found.
    """
    if not text:
        return None

    # Stricter pattern that avoids matching just 'INVOICE' followed by newline
    # Requires a label followed by at least 2 alphanumeric chars on the same line
    pattern = re.compile(
        r"\b(?:inv(?:oice)?|bill)\s*(?:no\.?|#|num(?:ber)?)?\s*[:\-]?\s*([A-Z0-9][-A-Z0-9/]{2,30})",
        re.IGNORECASE
    )

    for line in text.splitlines():
        line = line.strip()
        # Skip generic headers entirely (failure mode fix)
        if line.lower() in _SKIP_HEADERS:
            continue
            
        match = pattern.search(line)
        if match:
            # Additional guard: don't return the match if it's just a known header substring
            val = match.group(1).strip()
            if val.lower() not in _SKIP_HEADERS:
                return val

    return None


def extract_amounts(text: str) -> dict[str, float | None]:
    """
    Extract subtotal, GST/tax, and total amounts from raw OCR text.

    Uses case-insensitive keyword matching before each amount to correctly
    classify the value. The failure-mode fix for 'Total: None' is applied
    here — all keyword comparisons operate on lowercased text and the regex
    allows optional whitespace between the keyword and the colon/value.

    Args:
        text: Raw OCR output as a multi-line string.

    Returns:
        Dict with keys: 'subtotal', 'gst', 'total'.
        Each value is a float or None if not found.
    """
    # Search for each amount type
    total_match = _TOTAL_KEYWORDS.search(text)
    subtotal_match = _SUBTOTAL_KEYWORDS.search(text)
    gst_match = _GST_KEYWORDS.search(text)

    total = _parse_amount(total_match.group(1)) if total_match else None
    
    # --- Failure-Mode Fix: Global Max Fallback ---
    # SROIE receipts often separate labels and totals.
    # If keyword match failed, take the largest currency-formatted number near the bottom.
    if total is None:
        all_amounts = _AMOUNT_PATTERN.findall(text)
        if all_amounts:
            # Clean and parse all found amounts
            numeric_vals = []
            for m in all_amounts:
                v = _parse_amount(m)
                if v is not None:
                    numeric_vals.append(v)
            if numeric_vals:
                # Take the maximum of the last 4 amounts found (usually bottom of bill)
                total = max(numeric_vals[-4:])
    
    subtotal = _parse_amount(subtotal_match.group(1)) if subtotal_match else None
    gst = _parse_amount(gst_match.group(1)) if gst_match else None

    return {"subtotal": subtotal, "gst": gst, "total": total}


def parse_invoice(text: str) -> dict:
    """
    Master function: parse all fields from raw OCR text.

    Calls each extractor and assembles a single dict. Any field that cannot
    be extracted is set to None — the UI renders None fields as empty inputs,
    prompting the user to fill them manually (human-in-the-loop design).

    Args:
        text: Raw OCR output as a multi-line string (from ocr.extract_text).

    Returns:
        Dict with keys: vendor, date, invoice_number, subtotal, gst, total,
        raw_text. All values are str | float | None except raw_text (always str).
    """
    amounts = extract_amounts(text)
    return {
        "vendor": extract_vendor(text),
        "date": extract_date(text),
        "invoice_number": extract_invoice_number(text),
        "subtotal": amounts["subtotal"],
        "gst": amounts["gst"],
        "total": amounts["total"],
        "raw_text": text,
    }
