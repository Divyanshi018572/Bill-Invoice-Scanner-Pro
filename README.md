# 🧾 Invoice Scanner Pro

## 📖 Project Description
Invoice Scanner Pro is a highly capable, GPU-accelerated web application built on Streamlit and EasyOCR. It rapidly automates financial data processing by utilizing regex rules to extract vendor names, precise transaction dates, and total amounts directly from uploaded receipts and invoices. Featuring an interactive dashboard, users can easily perform human-in-the-loop data corrections, push verified information into a local SQLite database, and seamlessly export their records into instantly updated real-time CSV or Excel spreadsheets.

## 📂 Folder Structure

```text
Bill Invoice detector/
├── bill_scanner/             # Main Source Package
│   ├── app.py                # Streamlit Dashboard Entrypoint
│   ├── benchmark_sroie.py    # SROIE Benchmarking Script
│   ├── database.py           # SQLite Wrapper & Persistence 
│   ├── extractor.py          # Field Parsing & Regex Rules
│   └── ocr.py                # Wrapper around EasyOCR
├── SROIE_Dataset/            # Benchmark images and texts
├── tests/                    # Unit tests for the system
├── scripts/                  # Helper processing scripts
├── requirements.txt          # Python dependencies
├── LICENSE                   # Project software license
└── README.md                 # Project documentation
```

## ⚙️ Installation & Usage

1. **Install Requirements:**
   Make sure you have PyTorch installed for your specific CUDA version (e.g., cu118). Then install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Dashboard:**
   ```bash
   cd bill_scanner
   streamlit run app.py
   ```
