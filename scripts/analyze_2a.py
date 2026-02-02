
import pandas as pd

try:
    xl = pd.ExcelFile("debug_sheet.xlsx")
    df = xl.parse("2а. РАСЧЕТ БЛЮД 🍳")
    print("Columns:", list(df.columns)[:10]) # First 10
    print("\nFirst 10 Rows:\n", df.head(10).to_string())
            
except Exception as e:
    print(f"Error: {e}")
