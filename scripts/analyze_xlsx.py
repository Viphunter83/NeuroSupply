
import pandas as pd

try:
    xl = pd.ExcelFile("debug_sheet.xlsx")
    print("Sheet Names:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        if "ПЛАН" in sheet.upper() or "SALES" in sheet.upper() or "FORECAST" in sheet.upper():
            print(f"\n--- Analyzing Sheet: {sheet} ---")
            df = xl.parse(sheet)
            print(df.head(20).to_string())
            
except Exception as e:
    print(f"Error: {e}")
