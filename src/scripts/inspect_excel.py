import pandas as pd

file_path = "data_samples/Для_кафе_с_Ежедневными_поставками.xlsx"
df = pd.read_excel(file_path, header=None)
df = pd.read_excel(file_path, header=None)
print("Row 18:")
print(df.iloc[18])
