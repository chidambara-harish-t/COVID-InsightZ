import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_top10_px(latest_totals: pd.Series):
    """Plot top 10 regions by total cases (Plotly)."""
    import plotly.express as px
    import pandas as pd

    
    latest_totals = pd.to_numeric(latest_totals, errors="coerce").dropna()

    if latest_totals.empty:
        return px.bar(title="No valid data to display ")

    # Series DataFrame
    df = (
        latest_totals
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    if df.shape[1] == 2:
        df.columns = ["Region", "Total"]
    elif df.shape[1] == 3:
        df.columns = ["Country", "Province", "Total"]
        df["Region"] = df.apply(
            lambda r: f"{r['Country']} - {r['Province']}"
            if pd.notna(r["Province"]) and str(r["Province"]).lower() != "nan"
            and r["Province"] != r["Country"]
            else r["Country"],
            axis=1
        )
    else:
        
        df["Region"] = df.iloc[:, 0].astype(str)

    fig = px.bar(
        df,
        x="Region",
        y="Total",
        title="Top 10 Regions by Total Cases",
        labels={"Total": "Total Cases"},
        text="Total"
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(xaxis_tickangle=-30, height=420, margin=dict(l=10, r=10, t=30, b=30))
    return fig



def plot_daily_px(df: pd.DataFrame, countries: list[tuple[str, str]]):
    """Plot daily confirmed cases for selected countries/provinces (Plotly)."""
    plot_df = pd.DataFrame({
        "Date": df[("Date", "")],
    })

    #select regions 
    for c in countries:
        label = f"{c[0]} - {c[1]}" if c[1] and c[1] != c[0] else c[0]
        plot_df[label] = pd.to_numeric(df[c], errors="coerce")

    plot_df = plot_df.melt(id_vars="Date", var_name="Region", value_name="Cases")

    fig = px.line(
        plot_df,
        x="Date",
        y="Cases",
        color="Region",
        title="Daily COVID-19 Confirmed Cases",
        hover_data={"Date": "|%Y-%m-%d", "Cases": ":,"}
    )
    fig.update_layout(legend_title_text="Region", height=500)
    return fig


def plot_global_px(df: pd.DataFrame):
    """Plot global confirmed cases over time (Plotly)."""
    import plotly.express as px
    import pandas as pd

    
    if isinstance(df.columns, pd.MultiIndex):
        df_flat = df.copy()
        df_flat.columns = ['_'.join(filter(None, map(str, col))).strip() for col in df.columns]
    else:
        df_flat = df.copy()

    
    if "Date" not in df_flat.columns:
        df_flat = df_flat.rename(columns={"Date_": "Date"})
    if "GlobalCases" not in df_flat.columns and "GlobalCases_" in df_flat.columns:
        df_flat = df_flat.rename(columns={"GlobalCases_": "GlobalCases"})

    
    df_flat = df_flat.dropna(subset=["Date", "GlobalCases"])

    fig = px.line(
        df_flat,
        x="Date",
        y="GlobalCases",
        title="Global COVID-19 Confirmed Cases Over Time",
        hover_data={"Date": "|%Y-%m-%d", "GlobalCases": ":,"},
        color_discrete_sequence=["#1f77b4"]
    )
    fig.update_layout(height=500, xaxis_title="Date", yaxis_title="Confirmed Cases")
    return fig

# forecast plotly

def plot_forecast_px(df: pd.DataFrame, country: tuple[str, str]):
    """
    Plot 7-day rolling average and forecast for a country/province.
    Forecast: dashed red line + shaded background.
    Only shows 7d_avg + forecast (raw Cases omitted for clarity).
    """
    ts = df.copy()

    fig = go.Figure()

    # 7-day average line
    fig.add_trace(go.Scatter(
        x=ts["Date"], y=ts["7d_avg"],
        mode="lines",
        name="7d_avg",
        line=dict(color="orange", width=2)
    ))

    # Forecast line
    if "Forecast" in ts.columns and ts["Forecast"].notna().any():
        fig.add_trace(go.Scatter(
            x=ts["Date"], y=ts["Forecast"],
            mode="lines",
            name="Forecast",
            line=dict(color="red", dash="dash", width=3)
        ))

       
        forecast_start = ts["Date"].iloc[-7]
        forecast_end = ts["Date"].iloc[-1]
        fig.add_vrect(
            x0=forecast_start, x1=forecast_end,
            fillcolor="red", opacity=0.15,
            line_width=0,
            layer="below"
        )

    # Layout
    fig.update_layout(
        title=f"7-Day Rolling Avg & Forecast for {country[0]}" if not country[1] or str(country[1]).lower() == "nan"
              else f"7-Day Rolling Avg & Forecast for {country[0]} - {country[1]}",
        xaxis_title="Date",
        yaxis_title="Cases",
        hovermode="x unified",
        template="plotly_dark",
        height=420,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    return fig