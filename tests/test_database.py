"""
test_database.py — Assert-based tests for database.py.

Run with: pytest test_database.py -v
"""

import sys
from pathlib import Path
import os
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, save_invoice, fetch_all, delete_invoice, DB_PATH


def setup_function():
    """Wipe the database before each test to ensure a clean state."""
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_db()


# ---------------------------------------------------------------------------
# Test 1: init_db creates the table and fetch_all returns an empty DataFrame
# ---------------------------------------------------------------------------
def test_init_db_and_empty_fetch():
    """fetch_all must return an empty DataFrame with correct columns on new DB."""
    setup_function()
    df = fetch_all()
    assert isinstance(df, pd.DataFrame), "fetch_all must return a DataFrame"
    assert len(df) == 0, "New database must be empty"
    # Basic check for a couple of core columns
    assert "vendor" in df.columns, "Columns must match schema"
    assert "total" in df.columns, "Columns must match schema"
    print("PASS: test_init_db_and_empty_fetch")


# ---------------------------------------------------------------------------
# Test 2: save_invoice adds a row and fetch_all returns it
# ---------------------------------------------------------------------------
def test_save_and_fetch():
    """save_invoice must add a row and fetch_all must return it."""
    setup_function()
    sample_data = {
        "vendor": "Test Corp",
        "date": "2024-01-01",
        "invoice_number": "INV-TEST",
        "subtotal": 100.0,
        "gst": 5.0,
        "total": 105.0,
        "raw_text": "Full raw text for testing"
    }
    new_id = save_invoice(sample_data)
    assert isinstance(new_id, int), "save_invoice must return an integer ID"
    
    df = fetch_all()
    assert len(df) == 1, f"Expected 1 row, got {len(df)}"
    assert df.iloc[0]["vendor"] == "Test Corp", f"Expected 'Test Corp', got {df.iloc[0]['vendor']}"
    assert df.iloc[0]["total"] == 105.0, f"Expected 105.0, got {df.iloc[0]['total']}"
    print(f"PASS: test_save_and_fetch (ID: {new_id})")


# ---------------------------------------------------------------------------
# Test 3: delete_invoice removes a row and fetch_all reflects this
# ---------------------------------------------------------------------------
def test_delete_invoice():
    """delete_invoice must remove the specified row."""
    setup_function()
    sample_data = {"vendor": "Delete Me", "total": 99.0}
    new_id = save_invoice(sample_data)
    
    # Verify it exists
    df_before = fetch_all()
    assert len(df_before) == 1
    
    # Delete it
    delete_invoice(new_id)
    
    # Verify it's gone
    df_after = fetch_all()
    assert len(df_after) == 0, f"Expected 0 rows after delete, got {len(df_after)}"
    print(f"PASS: test_delete_invoice (ID: {new_id} removed)")


if __name__ == "__main__":
    test_init_db_and_empty_fetch()
    test_save_and_fetch()
    test_delete_invoice()
    print("\nAll database tests passed!")
