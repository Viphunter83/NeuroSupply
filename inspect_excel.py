import pandas as pd
try:
    df = pd.read_excel("data_samples/Для_кафе_с_Ежедневными_поставками.xlsx")
    print("Columns:", df.columns.tolist())
    print("First 2 rows:")
    print(df.iloc[10:20].to_dict())
except Exception as e:
    print(e)
