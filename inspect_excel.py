import glob
import os
import pandas as pd

files = glob.glob("data_samples/*.xlsx")
print(f"Found {len(files)} excel files.")

for f in files:
    try:
        print(f"\nChecking: {os.path.basename(f)}")
        xls = pd.ExcelFile(f)
        print(f"Sheets: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
            if "инструкция" in sheet.lower() or "instruction" in sheet.lower() or "intro" in sheet.lower():
                print(f"--- MATCH FOUND in {f} [{sheet}] ---")
                df = pd.read_excel(xls, sheet_name=sheet)
                print(df.head(20).to_string())
    except Exception as e:
        print(f"Error reading {f}: {e}")
