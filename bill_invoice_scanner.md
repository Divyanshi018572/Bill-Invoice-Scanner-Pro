# Project 01 — Bill / Invoice Scanner · Easy Tier

## What You Are Building

A Streamlit web application that accepts a photograph or scan of any printed bill, receipt, or GST invoice and automatically extracts structured fields — vendor name, invoice number, date, subtotal, GST amount, and total payable — from the raw image. The pipeline runs OCR to convert the image to text, then applies rule-based NLP parsing to locate and extract each field. All extracted records are persisted to a local SQLite database and can be exported as Excel or JSON at any time. The user can review and correct extracted fields before saving, making the system robust to OCR errors.

---

## Why This Architecture

A bill image is unstructured visual data — there is no schema, no fixed column positions, and no guaranteed layout across vendors. Two approaches exist: template matching (defining fixed regions per vendor layout) and OCR-plus-NLP (convert the entire image to text, then parse the text). Template matching breaks the moment a vendor changes their invoice design. OCR-plus-NLP is layout-agnostic — it works on any bill from any vendor as long as the text is readable.

PaddleOCR is chosen over Tesseract because it handles skewed, low-resolution, and partially degraded images significantly better out of the box, and it natively supports both printed and handwritten text. The preprocessing step — denoising, deskewing, adaptive thresholding — is essential because phone-camera bill photos have uneven lighting, slight rotation, and JPEG compression artifacts that reduce OCR accuracy by 20–40% if not corrected first.

The NLP extraction layer uses regex patterns and keyword matching rather than a trained NER model. This is the correct engineering decision for this tier: bills follow predictable text patterns ("Total: ₹1,250", "Invoice No. INV-2024-001") that regex handles reliably without requiring labeled training data or GPU inference. A trained model would add complexity without meaningfully improving accuracy on well-formatted printed bills.

SQLite is chosen for storage because it requires zero configuration, stores everything in a single file, and is directly queryable by pandas — which powers the dashboard and export functionality.

---

## Core Concepts to Understand Before Building

**1. OCR Pipeline**
Optical Character Recognition converts a raster image into a string of characters. Modern OCR engines like PaddleOCR use a detect-then-recognize pipeline: a text detection model first draws bounding boxes around text regions, then a recognition model reads the characters inside each box. The output is a list of (bounding_box, text, confidence_score) tuples. Confidence scores below 0.6 should be filtered — low-confidence results are usually noise, damaged characters, or background patterns mistaken for text.

**2. Image Preprocessing**
Raw bill photos fail OCR for three reasons: noise (camera grain, paper texture), skew (the camera was not perfectly parallel to the bill), and poor contrast (shadow across one side of the bill). Denoising smooths grain without blurring text. Deskew detects the dominant angle of text lines and rotates the image to make them horizontal. Adaptive thresholding converts the grayscale image to pure black-and-white, eliminating uneven lighting — this is more robust than a global threshold because it computes a local threshold per small region rather than one threshold for the entire image.

**3. Regex for Field Extraction**
Regular expressions match patterns in strings. For bill parsing, the pattern is always: find a keyword (e.g., "total", "invoice no"), then find the value immediately after it on the same line. Amount patterns must handle currency symbols, comma-separated thousands, and optional decimal points. Date patterns must handle multiple formats (DD/MM/YYYY, DD-Mon-YYYY, Mon DD YYYY). Build and test each pattern independently before combining them.

**4. SQLite with Python**
SQLite is a file-based relational database built into Python's standard library — no installation required. A connection opens the file (creating it if absent), a cursor executes SQL statements, and commit() writes changes to disk. The entire database is a single `.db` file that can be copied, backed up, or deleted like any other file. Pandas can read directly from SQLite via read_sql_query(), which returns a DataFrame — this makes the connection between storage and the dashboard seamless.

**5. Streamlit Application Structure**
Streamlit reruns the entire script top to bottom on every user interaction. This means state — like whether a file has been uploaded and processed — must be managed carefully. st.session_state persists values across reruns. The layout is controlled by st.columns() for side-by-side panels and st.expander() for collapsible sections. File uploads use st.file_uploader(), which returns a file-like object that can be passed directly to PIL.Image.open().

**6. Confidence-Based Validation**
Not every field will be extracted correctly from every bill. The system should surface its confidence to the user rather than silently returning wrong values. A field with no match returns None — the UI renders this as an empty input box, signaling the user to fill it manually. This human-in-the-loop design makes the system useful even when OCR or parsing fails partially.

---

## Project Workflow

### Phase 1 — OCR Engine Working

The goal of this phase is to get PaddleOCR installed and producing readable text from a bill photo. Do not build the UI yet. Work in a single script or notebook to isolate and validate the OCR output before building on top of it.

Collect 5 real bill photos to test with — phone camera shots of grocery receipts, utility bills, or restaurant bills. These should include at least one photo with slight skew and one with uneven lighting. These will serve as your evaluation set throughout the project.

Implement the preprocessing function. Apply it to each test image and visually inspect the preprocessed result — the output should look like clean black text on a white background. If the deskew step is over-rotating (straightening text that was already straight), add a rotation threshold: only rotate if the detected angle exceeds 1 degree.

Run PaddleOCR on both the raw image and the preprocessed image and compare the output. The preprocessed version should produce fewer garbled characters and higher average confidence scores. Log the full OCR output for each test bill — you will reference this when building the field extractor.

Success criterion: for each of your 5 test bills, PaddleOCR on the preprocessed image produces text that a human could read and extract a total amount from.

---

### Phase 2 — Field Extraction Working

The goal of this phase is to reliably extract vendor name, date, invoice number, total, GST, and subtotal from the raw OCR text. Work in isolation — use the OCR text strings you logged in Phase 1 as hardcoded inputs, not live OCR. This separates the parsing logic from the OCR dependency.

For each field, write the extraction function, test it against all 5 bill text strings, and record which bills it fails on and why. Fix the pattern or add a fallback before moving to the next field.

Vendor name extraction is the most heuristic: the first non-empty, non-numeric line is usually the company name. This fails for bills that begin with a header like "TAX INVOICE" — handle this by skipping known header strings before taking the first line.

Amount extraction must handle the following formats: "1,250.00", "1250", "₹ 1,250", "Rs.1250.50". Build one regex that handles all of these and test it against real values from your test bills.

Date extraction must handle at least three formats: DD/MM/YYYY, DD-MM-YYYY, and DD Mon YYYY (e.g., 15 Jan 2024). Use a list of patterns tried in sequence — return the first match.

Success criterion: for each of your 5 test bills, the extractor correctly identifies the total amount. Vendor, date, and invoice number are acceptable to miss on 1–2 bills — total amount must always be found.

---

### Phase 3 — Database and Export

The goal of this phase is a working SQLite database and export pipeline. Test this phase without the UI — write a small script that calls save_invoice() with hardcoded data, then calls fetch_all() and prints the result, then exports to Excel.

The database schema has one table: invoices. Columns are id (auto-increment primary key), vendor (text), invoice_number (text), date (text), subtotal (real), gst (real), total (real), raw_text (text), and created_at (timestamp with default current_timestamp). Store date as text — parsing it into a Python date object adds complexity with no benefit for this tier.

The Excel export uses pandas to_excel() with openpyxl as the engine. The JSON export uses pandas to_json() with orient="records" and indent=2. Both exports write to an exports/ directory. The download buttons in Streamlit read the file from disk and serve it — do not store binary data in session state.

Success criterion: save 3 invoices, run fetch_all(), confirm all 3 appear in the returned DataFrame, export to Excel, open the Excel file and confirm the data is correct.

---

### Phase 4 — Streamlit UI

The goal of this phase is to connect all three phases into a working application. The UI layout has a sidebar for file upload and a two-column main area: left column shows the uploaded image, right column shows the extracted and editable fields.

All extracted fields must be editable before saving. Use st.text_input() for text fields and st.number_input() for amount fields. Pre-fill each input with the extracted value. This is the most important UX decision in the project — users must be able to correct OCR errors before the data enters the database.

The bottom section of the page shows a summary metrics row (total invoices, total amount, total GST, unique vendors) followed by the full invoice table and download buttons.

Show a spinner during OCR and extraction — these operations take 2–5 seconds and the UI must communicate that processing is happening. Use st.spinner() wrapping the OCR and extraction calls.

Success criterion: upload a real bill photo, see the extracted fields pre-filled in the form, correct one field, click save, see the invoice appear in the table below, and successfully download the Excel export.

---

## Folder Structure

```
bill_scanner/
├── app.py                  ← Streamlit entry point, UI layout, page config
├── ocr.py                  ← PaddleOCR wrapper, text extraction functions
├── extractor.py            ← Regex field parser (vendor, date, amounts, invoice no.)
├── database.py             ← SQLite init, save, fetch, delete functions
├── utils.py                ← Image preprocessing (denoise, deskew, threshold)
├── requirements.txt
├── invoices.db             ← Created automatically on first run
├── exports/                ← Excel and JSON downloads written here
│   ├── invoices.xlsx
│   └── invoices.json
└── test_images/            ← Store your 5 test bill photos here during development
    └── .gitkeep
```

---

## File Responsibilities

**app.py** — Streamlit page configuration, sidebar upload widget, two-column layout, editable field form, save button, summary metrics, invoice table, download buttons. Imports from all other modules. Contains no business logic — only UI wiring.

**ocr.py** — PaddleOCR instance initialization (singleton pattern — initialize once, reuse). Function to extract full text string from a numpy image array. Function to extract text with bounding boxes and confidence scores for debugging. Confidence filtering (discard results below 0.6).

**extractor.py** — One function per field: extract_vendor(), extract_date(), extract_invoice_number(), extract_amounts(). One master function parse_invoice() that calls all of them and returns a single dict with all fields. All functions accept a raw text string and return a value or None. No imports from other project modules.

**database.py** — init_db() creates the invoices table if it does not exist. save_invoice() inserts one record and returns the new row id. fetch_all() returns a pandas DataFrame of all records ordered by id descending. delete_invoice() removes one record by id. All functions open and close their own connection — do not share connections across calls.

**utils.py** — preprocess_image() accepts an image file path string and returns a preprocessed numpy array ready for OCR. pil_to_cv2() converts a PIL Image to a cv2-compatible numpy array. These are pure functions with no side effects.

---

## Requirements

```
requirements.txt
----------------
paddlepaddle==2.6.1
paddleocr==2.7.3
opencv-python-headless==4.9.0.80
pillow==10.3.0
streamlit==1.35.0
pandas==2.2.2
openpyxl==3.1.2
numpy==1.26.4
```

---

## Known Failure Modes and Fixes

**OCR produces garbled text on a clear photo**
The image color mode is wrong. PaddleOCR expects BGR (OpenCV format). If you pass an RGB array (PIL default), colors are inverted and OCR quality drops significantly. Always convert PIL images to cv2 BGR format before passing to PaddleOCR.

**Deskew rotates a straight image by 45 degrees**
The minAreaRect angle computation has a quadrant ambiguity — it returns angles between -90 and 0. When the detected angle is close to -45, the correction formula flips. Add a guard: if the absolute angle is less than 1 degree, skip rotation entirely.

**Total amount extracted as None on every bill**
The keyword matching is case-sensitive and your bills use "TOTAL" (uppercase). Make all keyword comparisons case-insensitive by lowercasing the line before matching. Also check for whitespace between the keyword and the colon — "Total : ₹1,250" has a space before the colon that a tight regex will miss.

**Streamlit re-runs OCR on every interaction**
Streamlit reruns the full script on every widget interaction. Wrapping the OCR call in a function decorated with @st.cache_data and keyed on the file bytes prevents re-running OCR when the user edits a field. Cache the (raw_text, parsed_fields) result, not the image.

**Excel export fails with PermissionError**
The exports/invoices.xlsx file is open in Excel when the export runs. Write to a timestamped filename (e.g., invoices_20240115_143022.xlsx) instead of overwriting the same file each time.

**PaddleOCR download fails on first run behind a proxy**
PaddleOCR downloads model weights on first initialization. Behind a corporate proxy or on Kaggle, this may fail silently. Download the model weights manually from the PaddleOCR GitHub releases page and set the model_dir parameter in PaddleOCR() to point to the local directory.

---

## Upgrade Path After Basic Works

Once the basic version runs end-to-end on your 5 test bills, these extensions add real value in roughly increasing order of difficulty.

**Hindi/regional language support** — Change lang='en' to lang='hi' in PaddleOCR initialization. Test on bills with mixed Hindi and English text. The extraction regex patterns need no changes because amounts and dates are typically in numerals regardless of language.

**PDF support** — Use the pdf2image library to convert each page of a PDF to a PIL Image, then pass each page through the existing pipeline. Bills received by email are often PDFs — this extension makes the tool useful for accountants who receive digital invoices.

**Duplicate detection** — Hash the raw_text string using hashlib.md5() and store the hash in the database. Before saving, check if the hash already exists — if it does, warn the user that this bill appears to already be saved. This prevents double-counting when the same bill is uploaded twice.

**Confidence scoring per field** — Instead of returning None for missing fields, return a (value, confidence) tuple where confidence is 1.0 for exact regex matches, 0.7 for fuzzy matches, and 0.0 for no match. Display a color indicator next to each field in the UI (green for high confidence, yellow for medium, red for no match) so users know which fields to review carefully.

---

## Dataset and Test Resources

**Test data** — Collect your own bill photos using a phone camera. Target at least 10 diverse bills: grocery store receipts, utility bills, restaurant bills, GST invoices from e-commerce, and medical bills. Diversity in vendor, layout, and language makes your test set meaningful.

**SROIE Dataset** — A publicly available dataset of 1,000 scanned receipt images with ground truth annotations for vendor, date, address, and total. Available on Kaggle (search "SROIE receipt OCR"). Use this to benchmark your extractor's accuracy quantitatively — compute field-level accuracy (fraction of bills where the extracted value matches ground truth) for each field.

**PaddleOCR documentation** — github.com/PaddlePaddle/PaddleOCR — the README contains installation instructions, language support list, and a quickstart that matches exactly what this project needs.

---

## Checkpoint — Before Moving to Next Project

Answer these questions without looking at your code. If you cannot answer all of them confidently, revisit the relevant phase.

1. **Conceptual** — Explain why adaptive thresholding produces better OCR results than a global threshold on a bill photo taken with a phone camera. What property of phone-camera images makes global thresholding fail?

2. **Diagnostic** — Your extractor returns None for total on 3 out of 10 test bills. All 3 are from the same supermarket chain. What is the most likely reason, and what is your first debugging step?

3. **Engineering** — A user uploads the same bill twice in one session. The database currently saves it twice. Describe the exact change you would make to detect and prevent this duplicate, including which file you would modify and what new column you would add.

4. **Practical** — Your Streamlit app re-runs OCR every time the user clicks the save button, even though the image has not changed. Explain why this happens and describe the fix using st.cache_data.

5. **Extension** — A client asks you to process a folder of 500 PDF invoices overnight without any human review. Which parts of the current pipeline would break, which would work unchanged, and what would you add to make this work as a batch job?
