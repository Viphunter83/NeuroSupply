import pandas as pd
import os

files_to_inspect = [
    "data_samples/Для_кафе_с_Ежедневными_поставками.xlsx",
    "data_samples/NEW Ежедневный ВДНХ.xlsx"
]

for file_path in files_to_inspect:
    full_path = os.path.join(os.getcwd(), file_path)
    print(f"\n--- Inspecting {file_path} ---")
    if os.path.exists(full_path):
        try:
            # Read first few rows
            df = pd.read_excel(full_path, nrows=5)
            print("Columns:", df.columns.tolist())
            print(df.head())
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print("File not found.")
