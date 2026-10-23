"""Interactive, publication-grade data visualization library built with Plotly.
Implements high-contrast dark research styling, responsive layouts, annotations,
econometric markers, and purchasing power visualizations.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List, Dict, Any

# High-Contrast Research Palette Constants (Optimized for Dark Theme Legibility)
COLOR_EXPORTS = "#38bdf8"     # Electric Sky Blue
COLOR_IMPORTS = "#f87171"     # Vibrant Coral Red
COLOR_BALANCE = "#4ade80"     # Emerald Green (Surplus)
COLOR_DEFICIT = "#fb7185"     # Rose Crimson (Deficit)
COLOR_ACCENT = "#fbbf24"      # Bright Amber
COLOR_PURPLE = "#c084fc"      # Soft Violet
COLOR_TEAL = "#2dd4bf"        # Bright Teal
DARK_BG = "#0f172a"           # Deep Slate Navy
CARD_BG = "#1e293b"           # Slate Surface
GRID_COLOR = "#334155"        # Visible Slate Grid
TEXT_MAIN = "#f8fafc"         # Crisp White
TEXT_MUTED = "#cbd5e1"        # Light Slate

def get_base_layout(title: str = "", height: int = 480) -> dict:
    """Returns high-contrast, modern dark academic styling for Plotly figures."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family="Inter, Roboto, sans-serif", size=17, color=TEXT_MAIN),
            x=0.02,
            y=0.96
        ),
        template="plotly_dark",
        height=height,
        margin=dict(l=45, r=40, t=65, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=TEXT_MAIN, size=12)
        ),
        font=dict(family="Inter, Roboto, sans-serif", size=12, color=TEXT_MUTED),
        plot_bgcolor=DARK_BG,
        paper_bgcolor=DARK_BG,
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            color=TEXT_MUTED,
            tickfont=dict(color=TEXT_MUTED, size=11),
            linecolor=GRID_COLOR
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=True,
            zerolinecolor="#475569",
            color=TEXT_MUTED,
            tickfont=dict(color=TEXT_MUTED, size=11),
            linecolor=GRID_COLOR
        )
    )

def plot_macro_overview(df_macro: pd.DataFrame) -> go.Figure:
    """Plots long-run Exports, Imports, and Net Trade Balance."""
    fig = go.Figure()

    # Exports Line
    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["exports_usd_billion"],
        name="Total Exports (Goods & Services)",
        mode="lines+markers",
        line=dict(color=COLOR_EXPORTS, width=3.2),
        marker=dict(size=6, color=COLOR_EXPORTS),
        hovertemplate="<b>Year %{x}</b><br>Exports: $%{y:.1f}B<extra></extra>"
    ))

    # Imports Line
    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["imports_usd_billion"],
        name="Total Imports (Goods & Services)",
        mode="lines+markers",
        line=dict(color=COLOR_IMPORTS, width=3.2),
        marker=dict(size=6, color=COLOR_IMPORTS),
        hovertemplate="<b>Year %{x}</b><br>Imports: $%{y:.1f}B<extra></extra>"
    ))

    # Net Trade Balance Bar
    colors = [COLOR_BALANCE if val >= 0 else COLOR_DEFICIT for val in df_macro["trade_balance_usd_billion"]]
    fig.add_trace(go.Bar(
        x=df_macro["year"],
        y=df_macro["trade_balance_usd_billion"],
        name="Net Trade Balance",
        marker_color=colors,
        opacity=0.85,
        hovertemplate="<b>Year %{x}</b><br>Trade Balance: $%{y:.1f}B<extra></extra>"
    ))

    # Add historical shock annotations
    if 2008 in df_macro["year"].values:
        fig.add_vline(x=2008, line_dash="dash", line_color="#94a3b8")
        fig.add_annotation(x=2008, y=df_macro["imports_usd_billion"].max()*0.85, text="2008 Global Financial Crisis", showarrow=False, font=dict(size=11, color="#cbd5e1"))
    if 2020 in df_macro["year"].values:
        fig.add_vline(x=2020, line_dash="dash", line_color="#94a3b8")
        fig.add_annotation(x=2020, y=df_macro["imports_usd_billion"].max()*0.95, text="COVID-19 Pandemic Disruption", showarrow=False, font=dict(size=11, color="#cbd5e1"))
    if 2025 in df_macro["year"].values:
        fig.add_vline(x=2025, line_dash="dot", line_color=COLOR_ACCENT)
        fig.add_annotation(x=2025, y=df_macro["imports_usd_billion"].max()*0.75, text="FY25 Q1 (Apr-Jul)", showarrow=False, font=dict(size=11, color=COLOR_ACCENT))

    layout = get_base_layout("India's Long-Term Trade Trajectory (1995 - 2025) [USD Billions]")
    layout["yaxis"]["title"] = "Value (USD Billions)"
    fig.update_layout(layout)
    return fig

def plot_growth_rates(df_macro: pd.DataFrame) -> go.Figure:
    """Plots annual percentage growth rates for exports and imports."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_macro["year"],
        y=df_macro["exports_yoy_pct"],
        name="Exports YoY Growth (%)",
        marker_color=COLOR_EXPORTS,
        hovertemplate="<b>Year %{x}</b><br>Exports YoY: %{y:.1f}%<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=df_macro["year"],
        y=df_macro["imports_yoy_pct"],
        name="Imports YoY Growth (%)",
        marker_color=COLOR_IMPORTS,
        opacity=0.9,
        hovertemplate="<b>Year %{x}</b><br>Imports YoY: %{y:.1f}%<extra></extra>"
    ))

    layout = get_base_layout("Annual Trade Growth Rates (Year-over-Year %)")
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "Annual Growth Rate (%)"
    fig.update_layout(layout)
    return fig

def plot_openness_ratios(df_macro: pd.DataFrame) -> go.Figure:
    """Plots Trade-to-GDP Openness ratio alongside individual export and import shares."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["calculated_trade_openness_pct"],
        name="Trade Openness ((Exp + Imp) / GDP %)",
        mode="lines+markers",
        line=dict(color=COLOR_TEAL, width=3.5),
        marker=dict(size=6),
        hovertemplate="<b>Year %{x}</b><br>Trade Openness: %{y:.1f}%<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["exports_pct_gdp"],
        name="Exports / GDP (%)",
        mode="lines",
        line=dict(color=COLOR_EXPORTS, dash="dash", width=2.2),
        hovertemplate="<b>Year %{x}</b><br>Exports/GDP: %{y:.1f}%<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["imports_pct_gdp"],
        name="Imports / GDP (%)",
        mode="lines",
        line=dict(color=COLOR_IMPORTS, dash="dash", width=2.2),
        hovertemplate="<b>Year %{x}</b><br>Imports/GDP: %{y:.1f}%<extra></extra>"
    ))

    layout = get_base_layout("India's Trade Openness & Economic Integration (% of GDP)")
    layout["yaxis"]["title"] = "Share of GDP (%)"
    fig.update_layout(layout)
    return fig

def plot_partner_choropleth(df_bilateral_year: pd.DataFrame, metric: str = "total_trade_usd_million") -> go.Figure:
    """Renders world choropleth with dark high-contrast oceans and bright intensity."""
    title_map = {
        "total_trade_usd_million": "Total Bilateral Merchandise Trade Volume ($ Million)",
        "exports_usd_million": "Exports by Destination Country ($ Million)",
        "imports_usd_million": "Imports by Source Country ($ Million)",
        "trade_balance_usd_million": "Bilateral Trade Balance ($ Million - Surplus vs Deficit)"
    }
    
    color_scale = "Blues" if metric in ["exports_usd_million", "total_trade_usd_million"] else (
        "Reds" if metric == "imports_usd_million" else "RdYlGn"
    )

    fig = px.choropleth(
        df_bilateral_year,
        locations="iso3",
        color=metric,
        hover_name="country",
        hover_data={
            "exports_usd_million": ":,.1f",
            "imports_usd_million": ":,.1f",
            "trade_balance_usd_million": ":,.1f",
            "iso3": False
        },
        color_continuous_scale=color_scale,
        title=f"<b>{title_map.get(metric, 'Global Trade Intensity')}</b>"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_MAIN),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#64748b",
            projection_type="equirectangular",
            bgcolor=DARK_BG,
            lakecolor="#1e293b",
            landcolor="#1e293b",
            showocean=True,
            oceancolor="#090d16"
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=520
    )
    return fig

def plot_top_partners_bar(df_bilateral_year: pd.DataFrame, n: int = 10) -> go.Figure:
    """Grouped horizontal bar chart of top partners by exports and imports."""
    top_exp = df_bilateral_year.sort_values("exports_usd_million", ascending=False).head(n)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_exp["country"],
        x=top_exp["exports_usd_million"],
        name="Exports ($M)",
        orientation="h",
        marker_color=COLOR_EXPORTS,
        hovertemplate="<b>%{y}</b><br>Exports: $%{x:,.0f}M<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=top_exp["country"],
        x=top_exp["imports_usd_million"],
        name="Imports ($M)",
        orientation="h",
        marker_color=COLOR_IMPORTS,
        hovertemplate="<b>%{y}</b><br>Imports: $%{x:,.0f}M<extra></extra>"
    ))

    layout = get_base_layout(f"Top {n} Export Destinations vs Imports ($ Million)")
    layout["yaxis"]["autorange"] = "reversed"
    layout["barmode"] = "group"
    layout["xaxis"]["title"] = "USD Million"
    fig.update_layout(layout)
    return fig

def plot_commodity_breakdown(df_comm_year: pd.DataFrame, flow: str = "Export") -> go.Figure:
    """Horizontal bar chart showing commodity sector values and market shares."""
    sorted_df = df_comm_year.sort_values("value_usd_million", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=sorted_df["commodity_group"],
        x=sorted_df["value_usd_million"],
        orientation="h",
        marker_color=COLOR_EXPORTS if flow == "Export" else COLOR_IMPORTS,
        text=sorted_df["commodity_share_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        textfont=dict(color=TEXT_MAIN, size=11, family="Inter, sans-serif"),
        hovertemplate="<b>Sector: %{y}</b><br>Value: $%{x:,.1f}M<br>Flow Share: %{text}<extra></extra>"
    ))

    layout = get_base_layout(f"Principal Commodity Groups: {flow}s ($ Million & Flow Share %)")
    layout["xaxis"]["title"] = "USD Million"
    layout["height"] = max(440, len(sorted_df) * 36)
    fig.update_layout(layout)
    return fig

def plot_monthly_timeseries(df_monthly: pd.DataFrame) -> go.Figure:
    """Monthly merchandise trade series with 3-month and 12-month rolling trendlines."""
    fig = go.Figure()

    # Raw Monthly Exports and Imports
    fig.add_trace(go.Scatter(
        x=df_monthly["date"],
        y=df_monthly["merchandise_exports_usd_million"],
        name="Monthly Exports",
        mode="lines",
        line=dict(color=COLOR_EXPORTS, width=1.4),
        opacity=0.6,
        hovertemplate="Date: %{x|%b %Y}<br>Exports: $%{y:,.0f}M<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_monthly["date"],
        y=df_monthly["merchandise_imports_usd_million"],
        name="Monthly Imports",
        mode="lines",
        line=dict(color=COLOR_IMPORTS, width=1.4),
        opacity=0.6,
        hovertemplate="Date: %{x|%b %Y}<br>Imports: $%{y:,.0f}M<extra></extra>"
    ))

    # 12-Month Moving Averages (Smooth Trend)
    fig.add_trace(go.Scatter(
        x=df_monthly["date"],
        y=df_monthly["exports_12m_ma"],
        name="Exports (12M Secular Trend)",
        mode="lines",
        line=dict(color="#38bdf8", width=3.2),
        hovertemplate="Exports 12M MA: $%{y:,.0f}M<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_monthly["date"],
        y=df_monthly["imports_12m_ma"],
        name="Imports (12M Secular Trend)",
        mode="lines",
        line=dict(color="#fb7185", width=3.2),
        hovertemplate="Imports 12M MA: $%{y:,.0f}M<extra></extra>"
    ))

    layout = get_base_layout("High-Frequency Monthly Merchandise Trade & 12M Rolling Trend")
    layout["yaxis"]["title"] = "USD Million"
    fig.update_layout(layout)
    return fig

# ----------------------------------------------------
# INFLATION & PURCHASING POWER VISUALIZATIONS
# ----------------------------------------------------

def plot_cpi_inflation_trajectory(df_macro: pd.DataFrame) -> go.Figure:
    """Plots CPI Inflation time series with RBI 4% +/- 2% policy target corridor."""
    fig = go.Figure()

    # RBI Tolerance Band Shading (2% to 6%)
    fig.add_hrect(
        y0=2.0, y1=6.0,
        fillcolor="rgba(74, 222, 128, 0.12)",
        line_width=0,
        annotation_text="RBI Policy Target Band (4% ± 2%)",
        annotation_position="top left",
        annotation_font=dict(color="#4ade80", size=11)
    )
    fig.add_hline(y=4.0, line_dash="dot", line_color="#4ade80", line_width=1.5)

    # CPI Inflation Line
    fig.add_trace(go.Scatter(
        x=df_macro["year"],
        y=df_macro["cpi_inflation_pct"],
        name="CPI Inflation Rate (Annual %)",
        mode="lines+markers",
        line=dict(color=COLOR_ACCENT, width=3.2),
        marker=dict(size=6, color=COLOR_ACCENT),
        hovertemplate="<b>Year %{x}</b><br>CPI Inflation: %{y:.1f}%<extra></extra>"
    ))

    layout = get_base_layout("India's Consumer Price Index (CPI) Inflation Trajectory (1995-2025)")
    layout["yaxis"]["title"] = "Annual Inflation Rate (%)"
    fig.update_layout(layout)
    return fig

def plot_purchasing_power_decay(pp_df: pd.DataFrame, start_year: int, amount: float) -> go.Figure:
    """Visualizes the decay curve of real purchasing power of a fixed rupee amount over time."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pp_df["year"],
        y=pp_df["real_purchasing_power_inr"],
        name="Real Purchasing Power (₹)",
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.18)",
        line=dict(color=COLOR_EXPORTS, width=3.2),
        marker=dict(size=6, color=COLOR_EXPORTS),
        hovertemplate="<b>Year %{x}</b><br>Real Value: ₹%{y:,.2f}<br>Retention: %{customdata:.1f}%<extra></extra>",
        customdata=pp_df["purchasing_power_retention_pct"]
    ))

    # Add milestone annotations
    if not pp_df.empty:
        latest = pp_df.iloc[-1]
        fig.add_annotation(
            x=latest["year"],
            y=latest["real_purchasing_power_inr"],
            text=f"Today's Real Value:<br><b>₹{latest['real_purchasing_power_inr']:,.2f}</b> ({latest['purchasing_power_retention_pct']:.1f}%)",
            showarrow=True,
            arrowhead=2,
            arrowcolor=COLOR_ACCENT,
            font=dict(color=TEXT_MAIN, size=12),
            bgcolor=CARD_BG,
            bordercolor=GRID_COLOR
        )

    layout = get_base_layout(f"Purchasing Power Decay of ₹{amount:,.0f} Invested / Held in {start_year}")
    layout["yaxis"]["title"] = "Real Value in Constant Rupee Terms (₹)"
    fig.update_layout(layout)
    return fig

def plot_commodity_basket_comparison(basket_start: Dict[str, Any], basket_current: Dict[str, Any], year_start: int, year_current: int) -> go.Figure:
    """Compares the quantity of goods purchasable with the same amount across two eras."""
    items = list(basket_start.keys())
    qty_start = [basket_start[i]["quantity_affordable"] for i in items]
    qty_current = [basket_current[i]["quantity_affordable"] for i in items]
    units = [basket_start[i]["unit"] for i in items]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=items,
        x=qty_start,
        name=f"In Year {year_start}",
        orientation="h",
        marker_color=COLOR_TEAL,
        text=[f"{q} {u}" for q, u in zip(qty_start, units)],
        textposition="auto",
        hovertemplate=f"<b>%{{y}}</b> ({year_start}): %{{x}} units<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=items,
        x=qty_current,
        name=f"In Year {year_current} (Today)",
        orientation="h",
        marker_color=COLOR_DEFICIT,
        text=[f"{q} {u}" for q, u in zip(qty_current, units)],
        textposition="auto",
        hovertemplate=f"<b>%{{y}}</b> ({year_current}): %{{x}} units<extra></extra>"
    ))

    layout = get_base_layout(f"What Your Money Could Buy: {year_start} vs {year_current}")
    layout["barmode"] = "group"
    layout["xaxis"]["title"] = "Quantity Purchasable"
    layout["height"] = 420
    fig.update_layout(layout)
    return fig
