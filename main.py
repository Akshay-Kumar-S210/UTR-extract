from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime
import os
from typing import List, Dict, Any

app = FastAPI()

# Allow access from browser UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names for easier matching."""
    df.columns = [c.strip().lower().replace("_", " ") for c in df.columns]
    return df


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def parse_invoice_numbers(invoice_str: str) -> list:
    """Split comma-separated invoice numbers."""
    if pd.isna(invoice_str):
        return []
    parts = [s.strip() for s in str(invoice_str).split(",") if s.strip()]
    return parts


def expand_invoice_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Expand rows so each invoice number becomes a unique row."""
    expanded = []
    for _, row in df.iterrows():
        invoices = parse_invoice_numbers(row["invoice number"])
        if not invoices:
            expanded.append(row)
            continue
        for inv in invoices:
            new_row = row.copy()
            new_row["invoice number"] = inv
            expanded.append(new_row)
    return pd.DataFrame(expanded).reset_index(drop=True)


def convert_numpy(obj):
    """Convert NumPy and datetime objects to JSON-safe types."""
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime("%Y-%m-%d")
    if pd.isna(obj):
        return None
    return obj


def calculate_summary(before_df: pd.DataFrame, after_df: pd.DataFrame) -> Dict[str, Any]:
    """Return statistics for UI summary."""
    summary = {
        "original_rows": len(before_df),
        "expanded_rows": len(after_df),
        "unique_utrs": after_df["utr number"].nunique(),
        "unique_vendors": after_df["vendor name"].nunique(),
        "total_amount": after_df["amount"].sum(),
    }
    return {k: convert_numpy(v) for k, v in summary.items()}


@app.post("/process")
async def process_file(data_files: List[UploadFile] = File(...)):
    try:
        # Validate files
        if not data_files:
            return JSONResponse({"success": False, "error": "No files uploaded"}, status_code=400)

        df_combined = pd.DataFrame()

        for file in data_files:
            contents = await file.read()
            name = file.filename.lower()

            if name.endswith(".csv"):
                temp = pd.read_csv(io.BytesIO(contents))
            elif name.endswith((".xls", ".xlsx")):
                temp = pd.read_excel(io.BytesIO(contents))
            else:
                return JSONResponse({"success": False, "error": f"Unsupported file type: {name}"}, status_code=400)

            temp = normalize_columns(temp)
            df_combined = pd.concat([df_combined, temp], ignore_index=True)

        required = ["invoice number", "vendor name", "date", "utr number", "amount"]
        missing = [c for c in required if c not in df_combined.columns]
        if missing:
            return JSONResponse({"success": False, "error": f"Missing columns: {', '.join(missing)}"}, status_code=400)

        # Normalize and process
        df_combined["amount"] = df_combined["amount"].apply(safe_float)
        processed_df = expand_invoice_rows(df_combined)
        summary = calculate_summary(df_combined, processed_df)

        # Prepare preview rows
        preview = processed_df.head(15).to_dict(orient="records")
        preview = [{k: convert_numpy(v) for k, v in row.items()} for row in preview]

        # Create downloadable Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            processed_df.to_excel(writer, index=False, sheet_name="Processed_Data")

        encoded = base64.b64encode(output.getvalue()).decode("utf-8")
        filename = f"UTR_Number_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return JSONResponse(
            {
                "success": True,
                "summary": summary,
                "preview_data": preview,
                "filename": filename,
                "file_data": encoded,
                "message": f"Expanded {summary['original_rows']} rows → {summary['expanded_rows']} rows",
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the web interface."""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
