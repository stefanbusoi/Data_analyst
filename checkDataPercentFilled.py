import pandas as pd

if __name__=='__main__':
    df = pd.read_csv("presales_data_sample.csv")
    total_rows = len(df)
    print("Percent of fullness per category (column):")
    for col in df.columns:
        percent_filled = (df[col].count() / total_rows) * 100
        print(f"{col}: {percent_filled:.2f}%")
