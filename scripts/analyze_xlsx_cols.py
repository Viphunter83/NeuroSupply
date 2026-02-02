
import pandas as pd

try:
    xl = pd.ExcelFile("debug_sheet.xlsx")
    df = xl.parse("2. ПЛАН ПРОДАЖ 📅")
    print("Columns:", list(df.columns))
    print("\nFirst Row Full:\n", df.iloc[0])
            
except Exception as e:
    print(f"Error: {e}")
