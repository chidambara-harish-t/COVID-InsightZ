import matplotlib.pyplot as plt
import pandas as pd
from src.transform import format_region

def plot_daily(df: pd.DataFrame, countries: list[tuple[str, str]]):
    """Plot daily confirmed cases for selected regions (country or province)."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for c in countries:
        label = format_region(c)
        ax.plot(df[("Date", "")], pd.to_numeric(df[c], errors="coerce"), label=label)
    ax.set_xlabel("Date")
    ax.set_ylabel("Confirmed Cases")
    ax.legend()
    return fig

def plot_global(df: pd.DataFrame):
    """Plot global confirmed cases over time."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df[("Date", "")], df[("GlobalCases", "")], color="blue", label="Global Cases")
    ax.set_xlabel("Date")
    ax.set_ylabel("Confirmed Cases")
    ax.legend()
    return fig

def plot_top10(latest_totals: pd.Series):
    """Plot top 10 regions by total cases."""
    latest_totals = pd.to_numeric(latest_totals, errors="coerce").dropna()
    if latest_totals.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No valid data to display ", ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    # Format labels before plotting
    from src.transform import format_region
    latest_totals.index = [format_region(c) for c in latest_totals.index]

    sorted_totals = latest_totals.sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sorted_totals.plot(kind="bar", ax=ax, color="skyblue")
    ax.set_title("Top 10 Regions by Total Cases")
    ax.set_xlabel("Region")
    ax.set_ylabel("Total Cases")
    return fig