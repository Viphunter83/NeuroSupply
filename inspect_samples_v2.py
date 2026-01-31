
import pandas as pd
import os

files_to_inspect = [
    "data_samples/NEW Ежедневный ВДНХ.xlsx",
    "data_samples/Заказ продуктов ЕКТ 28.10.25.xlsx",
    "data_samples/Хозтовары ЕКАТ 28.10.25.xlsx"
]

for file_path in files_to_inspect:
    print(f"--- Inspecting {file_path} ---")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    try:
        # Read header only first to see structure
        df = pd.read_excel(file_path, header=None, nrows=10)
        print(df.to_string())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    print("\n")
