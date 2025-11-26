import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "CONVENIENT_global_confirmed_cases.csv"

def get_data(path: str | None = None):
    csv_path = Path(path) if path else DATA_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found at: {csv_path}")

    # Read  Country, Province
    df = pd.read_csv(csv_path, header=[0, 1])

    # Fill missing province names with country
    new_columns = []
    for country, province in df.columns:
        if country == "Country/Region":
            new_columns.append(("Date", ""))
        else:
            if not isinstance(province, str) or not province.strip():
                province = country
            new_columns.append((country, province))
    df.columns = pd.MultiIndex.from_tuples(new_columns)

    
    df[("Date", "")] = pd.to_datetime(df[("Date", "")], errors="coerce")
    df = df.dropna(subset=[("Date", "")])

    return df