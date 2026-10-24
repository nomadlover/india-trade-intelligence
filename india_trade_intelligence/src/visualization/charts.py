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
            text=f"Benchmark Year ({int(latest['year'])}) Value:<br><b>₹{latest['real_purchasing_power_inr']:,.2f}</b> ({latest['purchasing_power_retention_pct']:.1f}%)",
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
        name=f"In Base Year {year_start}",
        orientation="h",
        marker_color=COLOR_TEAL,
        text=[f"{q} {u}" for q, u in zip(qty_start, units)],
        textposition="auto",
        hovertemplate=f"<b>%{{y}}</b> ({year_start}): %{{x}} units<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=items,
        x=qty_current,
        name=f"In Benchmark Year {year_current}",
        orientation="h",
        marker_color=COLOR_DEFICIT,
        text=[f"{q} {u}" for q, u in zip(qty_current, units)],
        textposition="auto",
        hovertemplate=f"<b>%{{y}}</b> ({year_current}): %{{x}} units<extra></extra>"
    ))

    layout = get_base_layout(f"What Your Money Could Buy: Base Year {year_start} vs Benchmark Year {year_current}")
    layout["barmode"] = "group"
    layout["xaxis"]["title"] = "Quantity Purchasable"
    layout["height"] = 420
    fig.update_layout(layout)
    return fig


def plot_price_quantity_decomposition(df_decomp: pd.DataFrame, commodity: str, flow: str = "Export") -> go.Figure:
    """Plots log-additive Price vs Quantity decomposition and Unit Value trajectory."""
    df_sub = df_decomp[(df_decomp["commodity_group"] == commodity) & (df_decomp["trade_flow"] == flow)].copy()
    if df_sub.empty:
        df_sub = df_decomp[df_decomp["trade_flow"] == flow].copy()

    fig = go.Figure()
    if not df_sub.empty:
        # Grouped bar of Price Effect vs Quantity Effect
        fig.add_trace(go.Bar(
            x=df_sub["financial_year"],
            y=df_sub.get("price_effect_log_pct", [0]*len(df_sub)),
            name="Price (Unit Value) Effect (%)",
            marker_color=COLOR_ACCENT,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Price Effect: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_sub["financial_year"],
            y=df_sub.get("quantity_effect_log_pct", [0]*len(df_sub)),
            name="Quantity (Volume) Effect (%)",
            marker_color=COLOR_EXPORTS if flow == "Export" else COLOR_IMPORTS,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Quantity Effect: %{y:.1f}%<extra></extra>"
        ))
        # Total Value YoY Growth Line
        if "value_growth_pct" in df_sub.columns:
            fig.add_trace(go.Scatter(
                x=df_sub["financial_year"],
                y=df_sub["value_growth_pct"],
                name="Total Value Growth (%)",
                mode="lines+markers",
                line=dict(color=COLOR_BALANCE, width=2.5, dash="solid"),
                marker=dict(size=6, color=COLOR_BALANCE),
                hovertemplate="<b>%{x}</b><br>Value Growth: %{y:.1f}%<extra></extra>"
            ))

    layout = get_base_layout(f"Price vs Quantity Decomposition: {commodity} ({flow})", height=450)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "Annual Growth / Decomposition (%)"
    fig.update_layout(layout)
    return fig


def plot_energy_exposure_trajectory(df_energy: pd.DataFrame) -> go.Figure:
    """Plots Brent vs Indian Basket Crude pricing and Net Petroleum Bill."""
    fig = go.Figure()

    if not df_energy.empty:
        # Brent Benchmark Line
        fig.add_trace(go.Scatter(
            x=df_energy["year"],
            y=df_energy["brent_crude_usd_bbl"],
            name="Brent Crude ($/bbl)",
            mode="lines+markers",
            line=dict(color=COLOR_ACCENT, width=2.8),
            marker=dict(size=5, color=COLOR_ACCENT),
            hovertemplate="<b>%{x}</b><br>Brent: $%{y:.1f}/bbl<extra></extra>"
        ))
        # Indian Basket Crude Line
        fig.add_trace(go.Scatter(
            x=df_energy["year"],
            y=df_energy["indian_basket_crude_usd_bbl"],
            name="Indian Basket Crude ($/bbl)",
            mode="lines+markers",
            line=dict(color=COLOR_EXPORTS, width=2.8),
            marker=dict(size=5, color=COLOR_EXPORTS),
            hovertemplate="<b>%{x}</b><br>Indian Basket: $%{y:.1f}/bbl<extra></extra>"
        ))
        # Net Petroleum Import Bill Bar
        fig.add_trace(go.Bar(
            x=df_energy["year"],
            y=df_energy["net_petroleum_import_bill_usd_b"],
            name="Net Petroleum Bill ($B)",
            marker_color=COLOR_DEFICIT,
            opacity=0.75,
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Net Oil Bill: $%{y:.1f}B<extra></extra>"
        ))

    layout = get_base_layout("Energy Exposure: Global Crude Benchmarks vs Net Petroleum Bill", height=480)
    layout["yaxis"]["title"] = "Crude Oil Benchmark ($/bbl)"
    layout["yaxis2"] = dict(
        title="Net Oil Bill (US$ Billion)",
        overlaying="y",
        side="right",
        showgrid=False,
        color=TEXT_MUTED,
        tickfont=dict(color=TEXT_MUTED, size=11)
    )
    fig.update_layout(layout)
    return fig


def plot_external_sector_dashboard(df_ext: pd.DataFrame) -> go.Figure:
    """Plots FX Reserves buffer and Current Account Deficit (% GDP)."""
    fig = go.Figure()

    if not df_ext.empty:
        # FX Reserves Line
        fig.add_trace(go.Scatter(
            x=df_ext["year"],
            y=df_ext["foreign_exchange_reserves_usd_b"],
            name="FX Reserves ($B)",
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.15)",
            line=dict(color=COLOR_EXPORTS, width=3.0),
            marker=dict(size=5, color=COLOR_EXPORTS),
            hovertemplate="<b>%{x}</b><br>FX Reserves: $%{y:.1f}B<extra></extra>"
        ))
        # Inward Remittances Line
        if "inward_remittances_usd_b" in df_ext.columns:
            fig.add_trace(go.Scatter(
                x=df_ext["year"],
                y=df_ext["inward_remittances_usd_b"],
                name="Inward Remittances ($B)",
                mode="lines+markers",
                line=dict(color=COLOR_BALANCE, width=2.5, dash="dot"),
                marker=dict(size=4, color=COLOR_BALANCE),
                hovertemplate="<b>%{x}</b><br>Remittances: $%{y:.1f}B<extra></extra>"
            ))
        # Current Account Deficit (% GDP) Bar
        colors = [COLOR_BALANCE if val >= 0 else COLOR_DEFICIT for val in df_ext["current_account_deficit_pct_gdp"]]
        fig.add_trace(go.Bar(
            x=df_ext["year"],
            y=df_ext["current_account_deficit_pct_gdp"],
            name="CAD (% of GDP)",
            marker_color=colors,
            opacity=0.8,
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>CAD: %{y:.1f}% of GDP<extra></extra>"
        ))

    layout = get_base_layout("External Sector Resilience: FX Reserves & Current Account Deficit", height=480)
    layout["yaxis"]["title"] = "Foreign Exchange Reserves (US$ Billion)"
    layout["yaxis2"] = dict(
        title="Current Account Deficit (% of GDP)",
        overlaying="y",
        side="right",
        showgrid=False,
        color=TEXT_MUTED,
        tickfont=dict(color=TEXT_MUTED, size=11)
    )
    # Add horizontal warning line for CAD threshold at -2.5%
    fig.add_hline(y=-2.5, line_dash="dash", line_color=COLOR_DEFICIT, line_width=1.5, yref="y2",
                  annotation_text="Vulnerability Threshold (-2.5%)", annotation_position="bottom right",
                  annotation_font=dict(size=10, color=COLOR_DEFICIT))
    fig.update_layout(layout)
    return fig


def plot_partner_macro_matrix(df_partners: pd.DataFrame, year: int = 2024) -> go.Figure:
    """Plots Partner GDP Growth (%) and Manufacturing PMI across key trading partners."""
    df_yr = df_partners[df_partners["year"] == year].copy()
    if df_yr.empty and not df_partners.empty:
        df_yr = df_partners[df_partners["year"] == df_partners["year"].max()].copy()

    fig = go.Figure()
    if not df_yr.empty:
        fig.add_trace(go.Bar(
            x=df_yr["country_name"],
            y=df_yr["real_gdp_growth_pct"],
            name="Real GDP Growth (%)",
            marker_color=COLOR_TEAL,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>GDP Growth: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_yr["country_name"],
            y=df_yr["manufacturing_pmi"],
            name="Manufacturing PMI (50=Neutral)",
            marker_color=COLOR_PURPLE,
            opacity=0.85,
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Mfg PMI: %{y:.1f}<extra></extra>"
        ))

    layout = get_base_layout(f"Top Trading Partner Demand Conditions ({year})", height=420)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "Real GDP Growth Rate (%)"
    layout["yaxis2"] = dict(
        title="Manufacturing PMI (Diffusion Index)",
        overlaying="y",
        side="right",
        range=[40, 60],
        showgrid=False,
        color=TEXT_MUTED,
        tickfont=dict(color=TEXT_MUTED, size=11)
    )
    fig.add_hline(y=50.0, line_dash="dot", line_color="#94a3b8", line_width=1.5, yref="y2",
                  annotation_text="PMI Neutral (50.0)", annotation_position="top left",
                  annotation_font=dict(size=10, color="#94a3b8"))
    fig.update_layout(layout)
    return fig


def plot_economic_risk_gauges(df_risk: pd.DataFrame) -> go.Figure:
    """Plots Single-Supplier Critical Import Dependencies against the risk threshold."""
    if df_risk.empty:
        return go.Figure()

    latest_fy = df_risk["financial_year"].max()
    row = df_risk[df_risk["financial_year"] == latest_fy].iloc[0]

    items = [
        "China APIs (Pharma)",
        "China Solar Cells & Modules",
        "Australia Coking Coal",
        "Russia Crude Oil",
        "Switzerland Gold",
        "Russia/Saudi Fertilisers"
    ]
    shares = [
        row.get("api_china_share_pct", 68.0),
        row.get("solar_cells_china_share_pct", 62.0),
        row.get("coking_coal_australia_share_pct", 52.0),
        row.get("crude_oil_russia_share_pct", 36.8),
        row.get("gold_switzerland_share_pct", 38.0),
        row.get("fertiliser_top_supplier_share_pct", 31.5)
    ]
    colors = [COLOR_DEFICIT if s >= 50.0 else COLOR_ACCENT for s in shares]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=items,
        x=shares,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}%" for s in shares],
        textposition="auto",
        hovertemplate="<b>%{y}</b>: %{x:.1f}% of total Indian imports<extra></extra>"
    ))

    layout = get_base_layout(f"Single-Supplier Critical Import Dependency Shares ({latest_fy})", height=420)
    layout["xaxis"]["title"] = "Dominant Supplier Share of Indian Inward Volume (%)"
    layout["xaxis"]["range"] = [0, 80]
    fig.add_vline(x=50.0, line_dash="dash", line_color=COLOR_DEFICIT, line_width=1.8,
                  annotation_text="High Dependency Threshold (50%)", annotation_position="top right",
                  annotation_font=dict(size=10, color=COLOR_DEFICIT))
    fig.update_layout(layout)
    return fig


# =====================================================================
# MODULE A: INDIA TRADE DEPENDENCY MAP VISUALIZATIONS
# =====================================================================

def plot_dependency_concentration_treemap(
    df_partners: pd.DataFrame,
    commodity_group: str,
    trade_flow: str = "Import"
) -> go.Figure:
    """Generates a hierarchical treemap visualizing bilateral partner market shares for a commodity."""
    if df_partners is None or df_partners.empty:
        return go.Figure()

    df = df_partners.copy()
    labels = df["partner_country"].tolist()
    parents = ["" for _ in range(len(df))]
    values = df["value_usd_million"].tolist()
    shares = df["partner_share_pct"].tolist()

    hover_texts = [
        f"<b>{c}</b><br>Value: ${v:,.1f}M (${v/1000.0:.2f}B)<br>Market Share: {s:.1f}%"
        for c, v, s in zip(labels, values, shares)
    ]

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=hover_texts,
        textinfo="label+percent root",
        hoverinfo="text",
        marker=dict(
            colors=shares,
            colorscale=[[0.0, "#1e3a8a"], [0.5, "#0284c7"], [1.0, "#38bdf8"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Share (%)", font=dict(color=TEXT_MAIN, size=11)),
                tickfont=dict(color=TEXT_MUTED, size=10)
            )
        )
    ))

    layout = get_base_layout(f"{commodity_group} — Bilateral {trade_flow} Market Distribution", height=500)
    layout["margin"] = dict(l=15, r=15, t=55, b=15)
    fig.update_layout(layout)
    return fig


def plot_top_suppliers_bar(
    df_partners: pd.DataFrame,
    top_n: int = 10,
    trade_flow: str = "Import"
) -> go.Figure:
    """Plots ranked horizontal bar chart of top N partner countries with share percentages."""
    if df_partners is None or df_partners.empty:
        return go.Figure()

    df_top = df_partners.head(top_n).iloc[::-1]  # Reverse for top-at-top
    
    # Dynamic coloring: highlight lead partner with accent
    colors = [COLOR_EXPORTS if i < len(df_top) - 1 else COLOR_ACCENT for i in range(len(df_top))]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_top["partner_country"],
        x=df_top["partner_share_pct"],
        orientation="h",
        marker_color=colors,
        text=[f"  {s:.1f}% (${v:.2f}B)" for s, v in zip(df_top["partner_share_pct"], df_top["value_usd_billion"])],
        textposition="outside",
        textfont=dict(color=TEXT_MAIN, size=11),
        hovertemplate="<b>%{y}</b><br>Share: %{x:.2f}%<br>Value: $%{customdata:.2f}B<extra></extra>",
        customdata=df_top["value_usd_billion"]
    ))

    flow_label = "Suppliers" if "imp" in trade_flow.lower() else "Destinations"
    layout = get_base_layout(f"Top {len(df_top)} {flow_label} by Market Share (%)", height=420)
    layout["xaxis"]["title"] = "Share of India's Total Trade in Commodity (%)"
    max_share = df_top["partner_share_pct"].max()
    layout["xaxis"]["range"] = [0, max(max_share * 1.25, 20.0)]
    fig.update_layout(layout)
    return fig


def plot_historical_partner_share_trends(
    df_trend: pd.DataFrame,
    commodity_group: str,
    trade_flow: str = "Import"
) -> go.Figure:
    """Plots multi-year share evolution for top international trading partners."""
    if df_trend is None or df_trend.empty:
        return go.Figure()

    fig = go.Figure()
    palette = [COLOR_EXPORTS, COLOR_ACCENT, COLOR_PURPLE, COLOR_TEAL, COLOR_BALANCE, COLOR_DEFICIT]

    partners = df_trend["partner_country"].unique()
    for idx, partner in enumerate(partners):
        p_data = df_trend[df_trend["partner_country"] == partner].sort_values("financial_year")
        color = palette[idx % len(palette)]
        fig.add_trace(go.Scatter(
            x=p_data["financial_year"],
            y=p_data["partner_share_pct"],
            name=partner,
            mode="lines+markers",
            line=dict(width=2.5, color=color),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>{partner}</b> (%{{x}})<br>Share: %{{y:.1f}}%<br>Value: $%{{customdata:.2f}}B<extra></extra>",
            customdata=p_data["value_usd_billion"]
        ))

    layout = get_base_layout(f"{commodity_group} — Partner Market Share Evolution (FY14-FY26)", height=450)
    layout["yaxis"]["title"] = "Bilateral Market Share (%)"
    layout["xaxis"]["title"] = "Financial Year (April–March)"
    fig.update_layout(layout)
    return fig


def plot_hhi_trend(
    df_hhi: pd.DataFrame,
    commodity_group: str,
    trade_flow: str = "Import"
) -> go.Figure:
    """Plots HHI concentration index over time with international benchmark bands."""
    if df_hhi is None or df_hhi.empty:
        return go.Figure()

    fig = go.Figure()

    # Benchmark reference bands
    fig.add_hrect(y0=0, y1=1500, fillcolor="#10b981", opacity=0.08, line_width=0,
                  annotation_text="Diversified (< 1,500)", annotation_position="top left",
                  annotation_font=dict(color="#34d399", size=10))
    fig.add_hrect(y0=1500, y1=2500, fillcolor="#f59e0b", opacity=0.08, line_width=0,
                  annotation_text="Moderate (1,500 - 2,500)", annotation_position="top left",
                  annotation_font=dict(color="#fbbf24", size=10))
    fig.add_hrect(y0=2500, y1=10000, fillcolor="#ef4444", opacity=0.08, line_width=0,
                  annotation_text="High Concentration (>= 2,500)", annotation_position="top left",
                  annotation_font=dict(color="#f87171", size=10))

    # Benchmark lines
    fig.add_hline(y=1500, line_dash="dash", line_color="#f59e0b", line_width=1.2)
    fig.add_hline(y=2500, line_dash="dash", line_color="#ef4444", line_width=1.2)

    # Observed HHI Line
    fig.add_trace(go.Scatter(
        x=df_hhi["financial_year"],
        y=df_hhi["hhi_observed"],
        name="Observed HHI",
        mode="lines+markers",
        line=dict(color=COLOR_EXPORTS, width=3.2),
        marker=dict(size=7, color=COLOR_ACCENT),
        hovertemplate="<b>FY %{x}</b><br>HHI: %{y:,.1f}<br>Lead: %{customdata[0]} (%{customdata[1]:.1f}%)<extra></extra>",
        customdata=list(zip(df_hhi["top_1_partner"], df_hhi["top_1_share_pct"]))
    ))

    layout = get_base_layout(f"{commodity_group} ({trade_flow}) — Herfindahl-Hirschman Index Trajectory", height=450)
    layout["yaxis"]["title"] = "HHI Concentration Index (0 - 10,000)"
    layout["yaxis"]["range"] = [0, max(df_hhi["hhi_observed"].max() * 1.2, 3500)]
    layout["xaxis"]["title"] = "Financial Year (April–March)"
    fig.update_layout(layout)
    return fig


# =====================================================================
# MODULE B: TRADE SHOCK SIMULATOR VISUALIZATIONS
# =====================================================================

def plot_shock_comparison_waterfall(
    waterfall_data: List[Dict[str, Any]],
    title: str = "Trade Deficit Impact Waterfall ($B)"
) -> go.Figure:
    """Plots waterfall chart decomposing baseline deficit, crude shock, export shock, and scenario deficit."""
    if not waterfall_data:
        return go.Figure()

    x_labels = [item["step"] for item in waterfall_data]
    y_vals = [item["value_usd_b"] for item in waterfall_data]
    measures = ["absolute" if item["type"] in ("baseline", "total") else "relative" for item in waterfall_data]

    fig = go.Figure(go.Waterfall(
        name="Deficit Decomposition",
        orientation="v",
        measure=measures,
        x=x_labels,
        textposition="outside",
        text=[f"${abs(v):.1f}B" if v < 0 else f"+${v:.1f}B" for v in y_vals],
        textfont=dict(color=TEXT_MAIN, size=11),
        y=y_vals,
        connector=dict(line=dict(color="#475569", width=1.5)),
        increasing=dict(marker=dict(color=COLOR_BALANCE)),
        decreasing=dict(marker=dict(color=COLOR_DEFICIT)),
        totals=dict(marker=dict(color="#3b82f6"))
    ))

    layout = get_base_layout(title, height=450)
    layout["yaxis"]["title"] = "Net Merchandise Trade Balance (USD Billion)"
    fig.update_layout(layout)
    return fig


def plot_scenario_sensitivity_heatmap(
    sensitivity_df: pd.DataFrame,
    title: str = "Net Trade Deficit Impact Matrix ($B)"
) -> go.Figure:
    """Plots 2D sensitivity matrix cross-tabulating Crude Oil Shocks vs INR Depreciation."""
    if sensitivity_df is None or sensitivity_df.empty:
        return go.Figure()

    z_vals = sensitivity_df.values
    x_cols = sensitivity_df.columns.tolist()
    y_idx = sensitivity_df.index.tolist()

    # Annotations text formatted as +$X.XB or -$X.XB
    text_vals = [[f"{v:+.1f}B" for v in row] for row in z_vals]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=x_cols,
        y=y_idx,
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(family="Inter, sans-serif", size=12, color=TEXT_MAIN),
        colorscale=[
            [0.0, "#ef4444"],    # Heavy deficit expansion (red)
            [0.4, "#f97316"],    # Moderate deficit (orange)
            [0.6, "#eab308"],    # Neutral/mild (amber)
            [0.8, "#84cc16"],    # Minor surplus (light green)
            [1.0, "#22c55e"]     # Large surplus / terms of trade windfall (green)
        ],
        colorbar=dict(
            title=dict(text="Δ Deficit ($B)", font=dict(color=TEXT_MAIN, size=11)),
            tickfont=dict(color=TEXT_MUTED, size=10)
        ),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Deficit Impact: <b>%{z:+.2f} USD Billion</b><extra></extra>"
    ))

    layout = get_base_layout(title, height=480)
    layout["xaxis"]["title"] = "INR/USD Exchange Rate Depreciation"
    layout["yaxis"]["title"] = "Crude Oil Price Shock"
    fig.update_layout(layout)
    return fig


def plot_multi_scenario_comparison_bar(
    comparison_df: pd.DataFrame
) -> go.Figure:
    """Compares key trade aggregates across preset simulation scenarios."""
    if comparison_df is None or comparison_df.empty:
        return go.Figure()

    fig = go.Figure()
    scenarios = comparison_df["Scenario"].tolist()

    # Crude Oil Bill
    fig.add_trace(go.Bar(
        x=scenarios,
        y=comparison_df["Crude Oil Bill ($B)"],
        name="Crude Oil Bill ($B)",
        marker_color="#f97316",
        text=[f"${v:.1f}B" for v in comparison_df["Crude Oil Bill ($B)"]],
        textposition="auto"
    ))

    # Total Exports
    fig.add_trace(go.Bar(
        x=scenarios,
        y=comparison_df["Total Exports ($B)"],
        name="Total Exports ($B)",
        marker_color=COLOR_EXPORTS,
        text=[f"${v:.1f}B" for v in comparison_df["Total Exports ($B)"]],
        textposition="auto"
    ))

    # Net Trade Deficit (Magnitude)
    deficits = [abs(v) for v in comparison_df["Trade Balance ($B)"]]
    fig.add_trace(go.Bar(
        x=scenarios,
        y=deficits,
        name="Net Trade Deficit ($B)",
        marker_color=COLOR_DEFICIT,
        text=[f"${v:.1f}B" for v in deficits],
        textposition="auto"
    ))

    layout = get_base_layout("Macroeconomic Comparison Across Scenario Presets ($B)", height=480)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "USD Billion"
    fig.update_layout(layout)
    return fig


# =====================================================================
# MODULE C: DATA REVISION OBSERVATORY VISUALIZATIONS
# =====================================================================

def plot_revision_distribution_donut(summary: Dict[str, Any]) -> go.Figure:
    """Renders a donut chart illustrating added, removed, revised, and unchanged observations."""
    labels = ["Unchanged", "Revised", "Newly Added", "Removed"]
    values = [
        summary.get("unchanged_count", 0),
        summary.get("revised_count", 0),
        summary.get("added_count", 0),
        summary.get("removed_count", 0)
    ]
    colors = ["#334155", "#fbbf24", "#38bdf8", "#f87171"]

    # Filter out zeros for cleaner visualization if empty
    active_labels = [l for l, v in zip(labels, values) if v > 0]
    active_values = [v for v in values if v > 0]
    active_colors = [c for c, v in zip(colors, values) if v > 0]

    if not active_values:
        active_labels = ["No Data Compared"]
        active_values = [1]
        active_colors = ["#334155"]

    fig = go.Figure(data=[go.Pie(
        labels=active_labels,
        values=active_values,
        hole=0.62,
        marker=dict(colors=active_colors),
        textinfo="label+value+percent",
        textfont=dict(color=TEXT_MAIN, size=11),
        hovertemplate="<b>%{label}</b>: %{value} observations (%{percent})<extra></extra>"
    )])

    prev_v = summary.get("previous_version_id", "v-prev")
    new_v = summary.get("new_version_id", "v-new")
    layout = get_base_layout(f"Observation Delta Breakdown ({prev_v} → {new_v})", height=380)
    layout["annotations"] = [dict(
        text=f"<b>{summary.get('total_observations_compared', sum(values))}</b><br><span style='font-size:10px;color:#94a3b8;'>Compared</span>",
        x=0.5, y=0.5, font_size=16, font_color=TEXT_MAIN, showarrow=False
    )]
    fig.update_layout(layout)
    return fig


def plot_revision_diff_bars(df_revisions: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """Plots top absolute value revisions between versions with positive/negative color encoding."""
    if df_revisions is None or df_revisions.empty:
        return go.Figure()

    # Filter for non-null absolute revisions and sort by magnitude
    valid_revs = df_revisions[df_revisions["absolute_revision"].notna()].copy()
    if valid_revs.empty:
        return go.Figure()

    valid_revs["abs_magnitude"] = valid_revs["absolute_revision"].abs()
    top_df = valid_revs.sort_values(by="abs_magnitude", ascending=False).head(top_n).iloc[::-1]

    colors = [COLOR_BALANCE if v >= 0 else COLOR_DEFICIT for v in top_df["absolute_revision"]]

    labels = [
        f"{row['indicator_id'].replace('_', ' ').title()[:24]} ({row['reporting_period']})"
        for _, row in top_df.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=top_df["absolute_revision"],
        orientation="h",
        marker_color=colors,
        text=[f" {v:+.2f} ({row['percentage_revision']:+.1f}%)" if pd.notna(row['percentage_revision']) else f" {v:+.2f}"
              for v, row in zip(top_df["absolute_revision"], top_df.to_dict('records'))],
        textposition="auto",
        textfont=dict(color=TEXT_MAIN, size=11),
        hovertemplate="<b>%{y}</b><br>Revision: %{x:+.4f}<br>Prev: %{customdata[0]} → New: %{customdata[1]}<extra></extra>",
        customdata=list(zip(top_df["previous_value"], top_df["new_value"]))
    ))

    layout = get_base_layout(f"Top {len(top_df)} Value Revisions (Absolute Diff)", height=420)
    layout["xaxis"]["title"] = "Revision Magnitude (New Value − Previous Value)"
    fig.update_layout(layout)
    return fig


def plot_revision_classification_bar(df_revisions: pd.DataFrame) -> go.Figure:
    """Visualizes breakdown of detected changes by taxonomy classification."""
    if df_revisions is None or df_revisions.empty:
        return go.Figure()

    counts = df_revisions["revision_classification"].value_counts().reset_index()
    counts.columns = ["Classification", "Count"]

    color_map = {
        "OFFICIAL_SOURCE_REVISION": "#38bdf8",
        "NEW_OBSERVATION": "#4ade80",
        "PIPELINE_TRANSFORMATION_CORRECTION": "#fbbf24",
        "UNIT_NORMALIZATION_CHANGE": "#c084fc",
        "METHODOLOGY_CHANGE": "#f97316",
        "UNCLASSIFIED_VERSION_CHANGE": "#94a3b8"
    }
    colors = [color_map.get(c, "#64748b") for c in counts["Classification"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=counts["Classification"].str.replace("_", " "),
        y=counts["Count"],
        marker_color=colors,
        text=counts["Count"],
        textposition="outside",
        textfont=dict(color=TEXT_MAIN, size=11),
        hovertemplate="<b>%{x}</b>: %{y} records<extra></extra>"
    ))

    layout = get_base_layout("Revisions by Cause Classification", height=380)
    layout["yaxis"]["title"] = "Number of Revised Observations"
    fig.update_layout(layout)
    return fig


def plot_derived_metric_impact_waterfall(impacts: List[Dict[str, Any]]) -> go.Figure:
    """Visualizes how data revisions propagate to derived headline metrics."""
    if not impacts:
        return go.Figure()

    names = [item["metric_name"] for item in impacts]
    prev_vals = [item["previous_value"] for item in impacts]
    new_vals = [item["new_value"] for item in impacts]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names,
        y=prev_vals,
        name="Previous Vintage",
        marker_color="#475569",
        text=[f"${v:.1f}B" for v in prev_vals],
        textposition="auto"
    ))
    fig.add_trace(go.Bar(
        x=names,
        y=new_vals,
        name="Revised Vintage",
        marker_color=COLOR_EXPORTS,
        text=[f"${v:.1f}B" for v in new_vals],
        textposition="auto"
    ))

    layout = get_base_layout("Impact of Revisions on Headline Trade Aggregates ($B)", height=400)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "USD Billion"
    fig.update_layout(layout)
    return fig



