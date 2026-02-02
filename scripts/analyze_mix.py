
import pandas as pd

try:
    xl = pd.ExcelFile("debug_sheet.xlsx")
    df = xl.parse("3. ПРОДУКТОВЫЙ МИКС 📊")
    print("Columns:", list(df.columns)[:10])
    print("\nFirst 10 rows:\n", df.head(10).to_string())
            
except Exception as e:
    print(f"Error: {e}")
