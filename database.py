"""
database.py — SQLite database operations for the Bill/Invoice Scanner.

Responsibilities:
- init_db(): create the invoices table if it does not exist
- save_invoice(): insert one invoice record and return the new row id
- fetch_all(): return all records as a pandas DataFrame (ordered by id descending)
- delete_invoice(): remove one record by its id

Standard: 
- Each function opens and closes its own connection (thread-safe for Streamlit).
- No shared global connections.
"""

import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

# Database file path strictly relative to the project folder
DB_PATH = Path(__file__).parent / "invoices.db"


def init_db():
    """
    Initialize the SQLite database and create the invoices table if absent.

    Columns:
        - id: PK, auto-increment
        - file_name: TEXT (original image filename for benchmarking)
        - vendor: TEXT (company name)
        - invoice_number: TEXT (ref no)
        - date: TEXT (date as string)
        - subtotal: REAL
        - gst: REAL
        - total: REAL
        - raw_text: TEXT (stored for debugging/logging)
        - created_at: TIMESTAMP (defaults to NOW)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            vendor TEXT,
            invoice_number TEXT,
            date TEXT,
            subtotal REAL,
            gst REAL,
            total REAL,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_invoice(invoice_data: dict) -> int:
    """
    Insert a dictionary representing one invoice into the database.

    Args:
        invoice_data: Dict with keys: file_name, vendor, date, invoice_number,
                      subtotal, gst, total, raw_text.

    Returns:
        The id (int) of the newly created row.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (
            file_name, vendor, date, invoice_number, subtotal, gst, total, raw_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_data.get("file_name"),
        invoice_data.get("vendor"),
        invoice_data.get("date"),
        invoice_data.get("invoice_number"),
        invoice_data.get("subtotal"),
        invoice_data.get("gst"),
        invoice_data.get("total"),
        invoice_data.get("raw_text")
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def fetch_all() -> pd.DataFrame:
    """
    Fetch all invoice records as a pandas DataFrame.

    Order is strictly by ID descending (newest first).

    Returns:
        A pandas DataFrame containing all columns from the invoices table.
        Returns an empty DataFrame if no records exist.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM invoices ORDER BY id DESC", conn)
    conn.close()
    return df


def delete_invoice(invoice_id: int):
    """
    Delete a specific invoice record by its unique ID.

    Args:
        invoice_id: The primary key (id) of the row to remove.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
