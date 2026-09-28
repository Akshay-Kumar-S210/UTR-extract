# UTR Number Processor

A FastAPI web app that takes payment data files (CSV/Excel), splits rows containing comma-separated invoice numbers into one row per invoice, and returns a summary, a preview and a downloadable Excel report.

## Why this exists

Payment files often list several invoice numbers in a single cell against one UTR (bank transaction reference), for example `INV001, INV002, INV003`. That makes reconciliation, lookups and pivoting difficult. This tool expands each multi-invoice row into separate rows so every invoice can be tracked individually against its UTR.

## Features

- Upload one or more `.csv`, `.xls` or `.xlsx` files (drag and drop or browse)
- Combines multiple files into a single dataset
- Normalizes column names automatically (case, underscores and extra spaces)
- Validates that all required columns are present
- Expands comma-separated invoice numbers into individual rows
- Summary cards: original rows, expanded rows, unique UTRs, unique vendors, total amount, processed rows
- Preview of the first 15 processed rows
- One-click download of the processed data as an Excel file

## Required input columns

Each uploaded file must contain these columns (names are matched case-insensitively, and `_` is treated as a space):

| Column | Description |
|---|---|
| `Invoice Number` | One or more invoice numbers, separated by commas |
| `Vendor Name` | Name of the vendor |
| `Date` | Payment date |
| `UTR Number` | Bank transaction reference |
| `Amount` | Payment amount |

### Example

Input:

| Invoice Number | Vendor Name | Date | UTR Number | Amount |
|---|---|---|---|---|
| INV001, INV002 | ABC Traders | 2026-09-01 | UTR123456 | 5000 |

Output:

| invoice number | vendor name | date | utr number | amount |
|---|---|---|---|---|
| INV001 | ABC Traders | 2026-09-01 | UTR123456 | 5000 |
| INV002 | ABC Traders | 2026-09-01 | UTR123456 | 5000 |

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **Data processing:** pandas, NumPy, openpyxl
- **Frontend:** single HTML file with inline CSS and JavaScript, Font Awesome icons

## Project structure

```
UTR-extract/
├── main.py             # FastAPI app and processing logic
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web interface
└── static/
```

## Getting started

### Prerequisites

- Python 3.9 or later

### Installation

```bash
# Clone the repository
git clone https://github.com/Akshay-Kumar-S210/UTR-extract.git
cd UTR-extract

# (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### Run the app

```bash
python main.py
```

Then open **http://localhost:8000** in your browser.

## How to use

1. Open the app in your browser.
2. Drag and drop your payment data files, or click to browse.
3. Click **Process Files**.
4. Review the summary and the preview table.
5. Click **Download Processed Excel** to save the report.
6. Click **New Report** to start again.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web interface |
| `POST` | `/process` | Accepts `data_files` (multipart upload), returns JSON with summary, preview rows and the Excel file as base64 |

FastAPI's interactive docs are available at **http://localhost:8000/docs** while the app is running.

## Notes

- After expansion, each invoice row keeps the original row's amount. Keep this in mind when summing amounts, since a row split into several invoices will repeat its amount.
- The app is intended for local or internal use. If you deploy it, restrict the CORS settings in `main.py` (currently open to all origins).
