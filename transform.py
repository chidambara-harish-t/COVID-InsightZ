import pandas as pd

def format_region(col: tuple[str, str]) -> str:
    """Return a clean display name for a (country, province) column."""
    country, province = col
    if not province or str(province).lower() == "nan" or province.strip() == "" or province == country:
        return country
    return f"{country} - {province}"

def summary_stats(df: pd.DataFrame, countries: list[tuple[str, str]]):
    """Build summary stats for selected countries/provinces, with forecast columns."""
    summary = {"Region": [], "Total Cases": [], "Peak Cases": [], "Peak Date": [],
               "Last 7d Avg": [], "Projected Next 7d": []}

    for col in countries:
        series = pd.to_numeric(df[col], errors="coerce")

        total = series.sum(skipna=True)
        peak = series.max(skipna=True)
        peak_idx = series.idxmax() if peak > 0 else None

        # rolling average
        rolling = series.rolling(7, min_periods=1).mean()
        last_7d = rolling.iloc[-1] if not rolling.empty else 0

        # naive forecast = repeat last 7d avg
        projected = last_7d  

        summary["Region"].append(f"{col[0]} - {col[1]}" if col[1] not in [None, "nan", ""] else col[0])
        summary["Total Cases"].append(int(total) if pd.notna(total) else 0)
        summary["Peak Cases"].append(int(peak) if pd.notna(peak) else 0)
        summary["Peak Date"].append(
            df.loc[peak_idx, ("Date", "")].strftime("%Y-%m-%d") if peak_idx is not None else "N/A"
        )
        summary["Last 7d Avg"].append(int(last_7d))
        summary["Projected Next 7d"].append(int(projected))

    return pd.DataFrame(summary)


def global_cases(df: pd.DataFrame):
    """Add GlobalCases column = sum of all numeric columns by row."""
    numeric_df = df.drop(columns=[("Date", "")], axis=1, errors="ignore")
    df[("GlobalCases", "")] = numeric_df.sum(axis=1, numeric_only=True)
    return df

def forecast_7day(df: pd.DataFrame, region: tuple[str, str]):
    """
    Naive 7-day moving average forecast for one region (country, province).
    Handles 'nan' provinces.
    """
    country, province = region

    if province is None or str(province).lower() == "nan":
        col = (country, "nan")
        if col not in df.columns:
            col = (country, "")
    else:
        col = (country, province)

    if col not in df.columns:
        raise KeyError(f"Column {col} not found in DataFrame")

    # Extract time series
    ts = df[[("Date", ""), col]].copy()
    ts.columns = ["Date", "Cases"]

    #7-day rolling average
    ts["7d_avg"] = ts["Cases"].rolling(7, min_periods=1).mean()

    # Naive forecast for last 7-day avg forward
    last_date = ts["Date"].iloc[-1]
    last_avg = ts["7d_avg"].iloc[-1]

    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=7)
    future = pd.DataFrame({
        "Date": future_dates,
        "Cases": [None] * 7,
        "7d_avg": [last_avg] * 7,
        "Forecast": [last_avg] * 7
    })


    ts["Forecast"] = None
    ts = pd.concat([ts, future], ignore_index=True)

    return ts