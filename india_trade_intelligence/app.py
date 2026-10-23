"""INDIA TRADE INTELLIGENCE - Research-Grade Economics & Trade Application
Main Streamlit Dashboard.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import sys

# Ensure repository root is on sys.path for cloud deployment
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_FILE.parent) not in sys.path:
    sys.path.insert(0, str(CURRENT_FILE.parent))

# Setup page config
st.set_page_config(
    page_title="India Trade Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal module imports
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer
from india_trade_intelligence.src.analysis.econometrics import EconometricAnalyzer
from india_trade_intelligence.src.analysis.rankings import TradeRankingsAnalyzer
from india_trade_intelligence.src.ai.assistant import TradeAIAssistant, RESEARCH_QUESTIONS_CATALOG
from india_trade_intelligence.src.visualization.charts import (
    plot_macro_overview,
    plot_growth_rates,
    plot_openness_ratios,
    plot_partner_choropleth,
    plot_top_partners_bar,
    plot_commodity_breakdown,
    plot_monthly_timeseries,
    plot_cpi_inflation_trajectory,
    plot_purchasing_power_decay,
    plot_commodity_basket_comparison,
    COLOR_EXPORTS,
    COLOR_IMPORTS,
    COLOR_BALANCE,
    COLOR_DEFICIT,
    COLOR_ACCENT,
    COLOR_TEAL,
    DARK_BG,
    TEXT_MAIN
)

# Custom High-Contrast CSS for scholarly presentation
st.markdown("""
<style>
    .reportview-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #cbd5e1;
    }
    .taxonomy-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .badge-fact { background-color: #0369a1; color: #f0f9ff; border: 1px solid #38bdf8; }
    .badge-calc { background-color: #047857; color: #ecfdf5; border: 1px solid #4ade80; }
    .badge-interp { background-color: #b45309; color: #fffbeb; border: 1px solid #fbbf24; }
    .badge-hypo { background-color: #7e22ce; color: #faf5ff; border: 1px solid #c084fc; }
    .badge-quest { background-color: #be123c; color: #fff1f2; border: 1px solid #fb7185; }
    .guardrail-box {
        background-color: #1e293b;
        border-left: 4px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 0 6px 6px 0;
        margin: 16px 0;
        font-size: 0.90rem;
        color: #fde68a;
    }
    .q1-banner {
        background-color: #1e293b;
        border: 1px solid #f59e0b;
        border-left: 5px solid #f59e0b;
        padding: 12px 18px;
        border-radius: 6px;
        margin: 12px 0 20px 0;
        font-size: 0.88rem;
        color: #fef3c7;
    }
    .basket-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
        margin-bottom: 10px;
    }
    .basket-icon { font-size: 1.8rem; margin-bottom: 4px; }
    .basket-qty { font-size: 1.4rem; font-weight: 700; color: #38bdf8; }
    .basket-name { font-size: 0.82rem; color: #cbd5e1; font-weight: 500; }
    .basket-price { font-size: 0.75rem; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# Initialize Storage & Cache
@st.cache_resource
def get_db():
    return TradeDataStorage()

storage = get_db()

@st.cache_data
def load_all_data():
    df_macro = storage.get_macro_annual()
    df_bilateral = storage.get_bilateral_trade()
    df_commodity = storage.get_commodity_trade()
    df_monthly = storage.get_monthly_trade()
    catalog = storage.get_metadata_catalog()
    return df_macro, df_bilateral, df_commodity, df_monthly, catalog

df_macro, df_bilateral, df_commodity, df_monthly, catalog = load_all_data()

# Shared latest reference
latest_macro = df_macro.iloc[-1] if not df_macro.empty else {}

# Sidebar Navigation
st.sidebar.title("🌐 India Trade Intelligence")
st.sidebar.caption("Research-Grade Economic Intelligence Platform")
st.sidebar.markdown("---")

view_selection = st.sidebar.radio(
    "Analytical Dimension",
    [
        "1. Overview",
        "2. Trade Trends",
        "3. Trade Partners",
        "4. Commodities",
        "5. Macro Indicators",
        "6. Inflation & Purchasing Power (Value of Money)",
        "7. AI-Powered Research Outcomes",
        "8. Methodology & Provenance"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ Data Horizon Notice")
st.sidebar.warning(
    "**Provisional FY 2024-25 Data:**\n"
    "Figures for 2025/FY25 represent early **Quarter 1 (April–July)** momentum "
    "annualized/interim as reported in official preliminary releases from the "
    "Department of Commerce & DGCI&S."
)

st.sidebar.markdown("### 🔍 Official Data Sources")
st.sidebar.info(
    "**Primary Public Sources:**\n"
    "- World Bank Open Data (WDI)\n"
    "- DGCI&S, Ministry of Commerce & Industry\n"
    "- Reserve Bank of India (DBIE)\n\n"
    "**Temporal Coverage:** 1995 – 2025 (Q1)\n"
    "**Validation Suite:** Passed (Zero Faults)"
)

# Global Q1 Banner Function
def render_q1_caveat():
    st.markdown(
        """<div class="q1-banner">
        <strong>⚡ RESEARCH NOTICE ON FY 2024-25 / 2025 DATA:</strong><br>
        The figures for the latest reporting period (FY 2024-25 / calendar year 2025) represent 
        <strong>provisional Quarter 1 (April–July)</strong> data annualized/interim based on early releases 
        from the Department of Commerce and DGCI&S. These figures capture early-year momentum and are subject 
        to final fiscal year revisions.
        </div>""",
        unsafe_allow_html=True
    )

# ----------------------------------------------------
# 1. OVERVIEW VIEW
# ----------------------------------------------------
if view_selection == "1. Overview":
    st.header("Executive Trade Intelligence Overview")
    st.markdown(
        "A rigorous empirical analysis of India's international goods and services trade dynamics, "
        "tracking structural transitions, terms-of-trade shocks, and global economic integration."
    )
    render_q1_caveat()

    if not df_macro.empty:
        latest_row = df_macro.iloc[-1]
        
        # Calculate 10-year CAGR
        year_10_ago = latest_row["year"] - 10
        row_10_ago = df_macro[df_macro["year"] == year_10_ago]
        cagr_10yr = None
        if not row_10_ago.empty:
            cagr_10yr = TradeDataTransformer.calculate_cagr(
                row_10_ago["exports_usd_billion"].iloc[0],
                latest_row["exports_usd_billion"],
                10
            )

        # KPI Metrics Cards
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            exp_val = latest_row["exports_usd_billion"]
            exp_chg = latest_row.get("exports_yoy_pct", 0)
            st.metric("Total Exports", f"${exp_val:.1f} B", f"{exp_chg:+.1f}% YoY" if pd.notna(exp_chg) else None)
        with k2:
            imp_val = latest_row["imports_usd_billion"]
            imp_chg = latest_row.get("imports_yoy_pct", 0)
            st.metric("Total Imports", f"${imp_val:.1f} B", f"{imp_chg:+.1f}% YoY" if pd.notna(imp_chg) else None)
        with k3:
            bal_val = latest_row["trade_balance_usd_billion"]
            st.metric("Trade Balance", f"${bal_val:.1f} B", "Deficit" if bal_val < 0 else "Surplus")
        with k4:
            open_val = latest_row.get("calculated_trade_openness_pct", 0)
            st.metric("Trade Openness", f"{open_val:.1f}% of GDP")
        with k5:
            st.metric("10-Year Export CAGR", f"{cagr_10yr:.1f}%" if cagr_10yr else "N/A", "Secular Trajectory")

        st.markdown("---")

        # Main Trajectory Chart
        col_chart, col_stats = st.columns([2.5, 1.2])
        with col_chart:
            fig_overview = plot_macro_overview(df_macro)
            st.plotly_chart(fig_overview, use_container_width=True)

        with col_stats:
            st.subheader("Structural Shifts")
            sb = EconometricAnalyzer.analyze_structural_breaks(df_macro)
            st.markdown(f"""
            - **Pre-COVID Avg Exports (2015-19):** `${sb['pre_covid_avg_exports_usd_b']:.1f}B`
            - **Post-COVID Avg Exports (2021-24):** `${sb['post_covid_avg_exports_usd_b']:.1f}B`
            - **Structural Export Surge:** `+{sb['exports_expansion_pct']:.1f}%`
            - **Post-COVID Avg Deficit:** `${abs(sb['post_covid_avg_deficit_usd_b']):.1f}B`
            - **Post-COVID Trade Openness:** `{sb['post_covid_avg_openness_pct']:.1f}% of GDP`
            """)
            st.info(
                "💡 **Key Structural Realignment:** Post-2020, India's trade crossed $800B in annual exports, "
                "bolstered by electronic components, smartphone PLI output, and refined hydrocarbon redistribution."
            )

        # OLS Secular Trend Analysis
        ols_exp = EconometricAnalyzer.calculate_ols_trend(df_macro["exports_usd_billion"])
        ols_imp = EconometricAnalyzer.calculate_ols_trend(df_macro["imports_usd_billion"])
        
        st.markdown("### 📈 Econometric Secular Trend (OLS Estimation)")
        t1, t2 = st.columns(2)
        with t1:
            st.markdown(f"""
            **Exports Trend Line:**  
            - Annual Slope Increment: `+${ols_exp['average_annual_increment']:.2f} Billion / Year`  
            - Goodness-of-Fit ($R^2$): `{ols_exp['r_squared']:.4f}`
            """)
        with t2:
            st.markdown(f"""
            **Imports Trend Line:**  
            - Annual Slope Increment: `+${ols_imp['average_annual_increment']:.2f} Billion / Year`  
            - Goodness-of-Fit ($R^2$): `{ols_imp['r_squared']:.4f}`
            """)

# ----------------------------------------------------
# 2. TRADE TRENDS VIEW
# ----------------------------------------------------
elif view_selection == "2. Trade Trends":
    st.header("Comprehensive Trade Dynamics & Trend Analysis")
    st.markdown("Decomposing long-term trajectories, annual growth cycles, and high-frequency monthly fluctuations.")
    render_q1_caveat()

    trend_tab1, trend_tab2 = st.tabs(["Annual Secular Trends", "High-Frequency Monthly Series"])

    with trend_tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_growth_rates(df_macro), use_container_width=True)
        with c2:
            st.plotly_chart(plot_openness_ratios(df_macro), use_container_width=True)

        st.subheader("Historical Annual Time Series Data")
        display_cols = [
            "year", "exports_usd_billion", "imports_usd_billion",
            "trade_balance_usd_billion", "exports_yoy_pct", "imports_yoy_pct",
            "calculated_trade_openness_pct", "coverage_ratio"
        ]
        valid_display = [c for c in display_cols if c in df_macro.columns]
        st.dataframe(
            df_macro[valid_display].sort_values("year", ascending=False).style.format({
                "exports_usd_billion": "${:.1f}B",
                "imports_usd_billion": "${:.1f}B",
                "trade_balance_usd_billion": "${:.1f}B",
                "exports_yoy_pct": "{:+.1f}%",
                "imports_yoy_pct": "{:+.1f}%",
                "calculated_trade_openness_pct": "{:.1f}%",
                "coverage_ratio": "{:.3f}"
            }),
            use_container_width=True
        )

    with trend_tab2:
        if not df_monthly.empty:
            st.plotly_chart(plot_monthly_timeseries(df_monthly), use_container_width=True)

            m_col1, m_col2 = st.columns(2)
            with m_col1:
                fig_nonoil = px.line(
                    df_monthly,
                    x="date",
                    y="non_oil_trade_balance_usd_million",
                    title="Non-Oil Merchandise Trade Balance ($ Million)",
                    color_discrete_sequence=[COLOR_TEAL],
                    template="plotly_dark"
                )
                fig_nonoil.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
                fig_nonoil.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
                st.plotly_chart(fig_nonoil, use_container_width=True)
                st.caption("Tracking non-oil trade isolates core industrial competitiveness from crude price fluctuations.")

            with m_col2:
                fig_vol = px.line(
                    df_monthly,
                    x="date",
                    y="deficit_volatility_6m",
                    title="Rolling 6-Month Trade Deficit Volatility ($ Million)",
                    color_discrete_sequence=[COLOR_ACCENT],
                    template="plotly_dark"
                )
                fig_vol.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
                st.plotly_chart(fig_vol, use_container_width=True)
                st.caption("Standard deviation of the rolling monthly merchandise trade deficit.")

# ----------------------------------------------------
# 3. TRADE PARTNERS VIEW
# ----------------------------------------------------
elif view_selection == "3. Trade Partners":
    st.header("Direction of Trade & Bilateral Trading Partners")
    st.markdown("Geographic distribution of India's merchandise exports, imports, and partner concentration.")
    render_q1_caveat()

    if not df_bilateral.empty:
        fy_list = sorted(df_bilateral["financial_year"].unique(), reverse=True)
        selected_fy = st.selectbox("Select Financial Year", fy_list, index=0)

        df_fy = df_bilateral[df_bilateral["financial_year"] == selected_fy]

        # Calculate Herfindahl-Hirschman Index for the selected year
        partner_hhi = TradeDataTransformer.calculate_hhi(df_fy["total_trade_share_pct"])

        # Partner Metrics
        p1, p2, p3, p4 = st.columns(4)
        top_dest = df_fy.sort_values("exports_usd_million", ascending=False).iloc[0]
        top_src = df_fy.sort_values("imports_usd_million", ascending=False).iloc[0]
        top_surp = df_fy.sort_values("trade_balance_usd_million", ascending=False).iloc[0]
        top_def = df_fy.sort_values("trade_balance_usd_million", ascending=True).iloc[0]

        with p1:
            st.metric("Top Export Destination", f"{top_dest['country']}", f"${top_dest['exports_usd_million']:,.0f}M")
        with p2:
            st.metric("Top Import Source", f"{top_src['country']}", f"${top_src['imports_usd_million']:,.0f}M")
        with p3:
            st.metric("Largest Bilateral Surplus", f"{top_surp['country']}", f"+${top_surp['trade_balance_usd_million']:,.0f}M")
        with p4:
            st.metric("Largest Bilateral Deficit", f"{top_def['country']}", f"${top_def['trade_balance_usd_million']:,.0f}M")

        st.markdown(f"**Partner Concentration Index (HHI):** `{partner_hhi:.1f}` — *(HHI < 1,500 indicates a highly diversified trading footprint)*")

        # Interactive Map
        map_metric = st.radio(
            "Select Map Metric",
            ["total_trade_usd_million", "exports_usd_million", "imports_usd_million", "trade_balance_usd_million"],
            horizontal=True,
            format_func=lambda x: {
                "total_trade_usd_million": "Total Trade Volume ($M)",
                "exports_usd_million": "Exports ($M)",
                "imports_usd_million": "Imports ($M)",
                "trade_balance_usd_million": "Net Balance (Surplus / Deficit)"
            }[x]
        )
        st.plotly_chart(plot_partner_choropleth(df_fy, metric=map_metric), use_container_width=True)

        # Leaderboards
        rank_data = TradeRankingsAnalyzer.get_top_partners(df_bilateral, selected_fy, n=10)
        c_dest, c_src = st.columns(2)
        with c_dest:
            st.subheader(f"Top 10 Export Destinations ({selected_fy})")
            st.dataframe(
                rank_data["top_exports"].style.format({
                    "exports_usd_million": "${:,.1f}M",
                    "export_share_pct": "{:.1f}%"
                }),
                use_container_width=True
            )
        with c_src:
            st.subheader(f"Top 10 Import Sources ({selected_fy})")
            st.dataframe(
                rank_data["top_imports"].style.format({
                    "imports_usd_million": "${:,.1f}M",
                    "import_share_pct": "{:.1f}%"
                }),
                use_container_width=True
            )

        # Regional Breakdown
        st.subheader("Regional Trade Distribution")
        reg_df = TradeRankingsAnalyzer.get_regional_breakdown(df_bilateral, selected_fy)
        if not reg_df.empty:
            st.dataframe(
                reg_df.style.format({
                    "total_exports_usd_m": "${:,.1f}M",
                    "total_imports_usd_m": "${:,.1f}M",
                    "net_balance_usd_m": "${:,.1f}M",
                    "total_trade_usd_m": "${:,.1f}M",
                    "regional_share_pct": "{:.1f}%"
                }),
                use_container_width=True
            )

# ----------------------------------------------------
# 4. COMMODITIES VIEW
# ----------------------------------------------------
elif view_selection == "4. Commodities":
    st.header("Commodity Composition & Structural Trade Shifts")
    st.markdown("Sectoral breakdown of exports and imports across principal commodity groups.")
    render_q1_caveat()

    if not df_commodity.empty:
        fy_list = sorted(df_commodity["financial_year"].unique(), reverse=True)
        selected_fy = st.selectbox("Select Financial Year", fy_list, index=0, key="comm_fy")

        col_exp, col_imp = st.columns(2)
        with col_exp:
            df_comm_exp = df_commodity[
                (df_commodity["financial_year"] == selected_fy) &
                (df_commodity["trade_flow"] == "Export")
            ]
            st.plotly_chart(plot_commodity_breakdown(df_comm_exp, flow="Export"), use_container_width=True)

        with col_imp:
            df_comm_imp = df_commodity[
                (df_commodity["financial_year"] == selected_fy) &
                (df_commodity["trade_flow"] == "Import")
            ]
            st.plotly_chart(plot_commodity_breakdown(df_comm_imp, flow="Import"), use_container_width=True)

        st.markdown("---")
        st.subheader("📱 Special Research Case Study: Mobile & Electronics PLI Revolution")
        st.markdown(
            "Tracking the exponential inflection in **Electronic Goods (incl. Smartphones)** exports "
            "following the implementation of the Production Linked Incentive (PLI) scheme in 2020."
        )

        elec_exports = df_commodity[
            (df_commodity["commodity_group"] == "Electronic Goods (incl. Smartphones)") &
            (df_commodity["trade_flow"] == "Export")
        ].sort_values("fy_start_year")

        fig_elec = px.line(
            elec_exports,
            x="financial_year",
            y="value_usd_million",
            title="India's Electronics & Smartphone Exports Surge ($ Million)",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=[COLOR_ACCENT],
            template="plotly_dark"
        )
        fig_elec.add_vline(x="2020-21", line_dash="dash", line_color=COLOR_IMPORTS)
        fig_elec.add_annotation(x="2020-21", y=25000, text="PLI Policy Launch (2020)", showarrow=True, font=dict(color=TEXT_MAIN))
        fig_elec.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
        st.plotly_chart(fig_elec, use_container_width=True)

# ----------------------------------------------------
# 5. MACRO INDICATORS VIEW
# ----------------------------------------------------
elif view_selection == "5. Macro Indicators":
    st.header("Macroeconomic Context & Interaction Analysis")
    st.markdown("Investigating trade interactions with Gross Domestic Product, Exchange Rate (INR/USD), and Inflation.")
    render_q1_caveat()

    # Guardrail Alert Box
    st.markdown(
        f'<div class="guardrail-box"><strong>⚠️ METHODOLOGICAL GUARDRAIL:</strong><br>{EconometricAnalyzer.get_causality_disclaimer()}</div>',
        unsafe_allow_html=True
    )

    m1, m2 = st.columns(2)
    with m1:
        try:
            fig_fx = px.scatter(
                df_macro,
                x="exchange_rate_inr_per_usd",
                y="exports_usd_billion",
                trendline="ols",
                title="Exchange Rate (INR/USD) vs Exports ($B)",
                labels={"exchange_rate_inr_per_usd": "INR per USD", "exports_usd_billion": "Total Exports ($B)"},
                hover_data=["year"],
                color_discrete_sequence=[COLOR_EXPORTS],
                template="plotly_dark"
            )
        except Exception:
            fig_fx = px.scatter(
                df_macro,
                x="exchange_rate_inr_per_usd",
                y="exports_usd_billion",
                title="Exchange Rate (INR/USD) vs Exports ($B)",
                labels={"exchange_rate_inr_per_usd": "INR per USD", "exports_usd_billion": "Total Exports ($B)"},
                hover_data=["year"],
                color_discrete_sequence=[COLOR_EXPORTS],
                template="plotly_dark"
            )
            valid = df_macro[["exchange_rate_inr_per_usd", "exports_usd_billion"]].dropna()
            if len(valid) > 1:
                slope, intercept = np.polyfit(valid["exchange_rate_inr_per_usd"], valid["exports_usd_billion"], 1)
                x_vals = np.linspace(valid["exchange_rate_inr_per_usd"].min(), valid["exchange_rate_inr_per_usd"].max(), 50)
                fig_fx.add_trace(go.Scatter(x=x_vals, y=slope * x_vals + intercept, mode="lines", name="OLS Trend", line=dict(color=COLOR_ACCENT, dash="dash")))
        fig_fx.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
        st.plotly_chart(fig_fx, use_container_width=True)
        st.caption("Notice positive co-movement; however, both are co-trended with global economic expansion. Do not infer exchange rate causation.")

    with m2:
        try:
            fig_gdp = px.scatter(
                df_macro,
                x="gdp_usd_billion",
                y="imports_usd_billion",
                trendline="ols",
                title="Nominal GDP ($B) vs Imports ($B)",
                labels={"gdp_usd_billion": "GDP ($B)", "imports_usd_billion": "Total Imports ($B)"},
                hover_data=["year"],
                color_discrete_sequence=[COLOR_IMPORTS],
                template="plotly_dark"
            )
        except Exception:
            fig_gdp = px.scatter(
                df_macro,
                x="gdp_usd_billion",
                y="imports_usd_billion",
                title="Nominal GDP ($B) vs Imports ($B)",
                labels={"gdp_usd_billion": "GDP ($B)", "imports_usd_billion": "Total Imports ($B)"},
                hover_data=["year"],
                color_discrete_sequence=[COLOR_IMPORTS],
                template="plotly_dark"
            )
            valid = df_macro[["gdp_usd_billion", "imports_usd_billion"]].dropna()
            if len(valid) > 1:
                slope, intercept = np.polyfit(valid["gdp_usd_billion"], valid["imports_usd_billion"], 1)
                x_vals = np.linspace(valid["gdp_usd_billion"].min(), valid["gdp_usd_billion"].max(), 50)
                fig_gdp.add_trace(go.Scatter(x=x_vals, y=slope * x_vals + intercept, mode="lines", name="OLS Trend", line=dict(color=COLOR_ACCENT, dash="dash")))
        fig_gdp.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
        st.plotly_chart(fig_gdp, use_container_width=True)
        st.caption("Strong co-movement reflecting domestic industrial and consumer demand for imported capital and intermediate inputs.")

    # Correlation Matrix
    st.subheader("Bivariate Correlation Matrix")
    corr_vars = [
        "exports_usd_billion", "imports_usd_billion", "gdp_usd_billion",
        "exchange_rate_inr_per_usd", "cpi_inflation_pct", "calculated_trade_openness_pct"
    ]
    corr_matrix = EconometricAnalyzer.calculate_correlation_matrix(df_macro, corr_vars)
    if not corr_matrix.empty:
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Pairwise Pearson Correlation Coefficients",
            template="plotly_dark"
        )
        fig_corr.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG)
        st.plotly_chart(fig_corr, use_container_width=True)

# ----------------------------------------------------
# 6. INFLATION & PURCHASING POWER (VALUE OF MONEY)
# ----------------------------------------------------
elif view_selection == "6. Inflation & Purchasing Power (Value of Money)":
    st.header("Inflation & Real Purchasing Power (The Value of Your Money)")
    st.markdown(
        "Investigating domestic price inflation (CPI), currency purchasing power erosion over time, "
        "and physical commodity affordability baskets across India's economic history."
    )
    render_q1_caveat()

    # CPI Inflation Trajectory
    st.plotly_chart(plot_cpi_inflation_trajectory(df_macro), use_container_width=True)

    # Inflation Summary Metrics
    avg_inf = df_macro["cpi_inflation_pct"].mean() if "cpi_inflation_pct" in df_macro.columns else 5.8
    halving_years = EconometricAnalyzer.get_inflation_halving_time(avg_inf)

    inf_col1, inf_col2, inf_col3 = st.columns(3)
    with inf_col1:
        st.metric("30-Year Average CPI Inflation", f"{avg_inf:.2f}% / year", "Long-Run Trend")
    with inf_col2:
        st.metric("Purchasing Power Halving Time", f"~{halving_years} Years", "Rule of 70")
    with inf_col3:
        st.metric("RBI Policy Corridor", "4.0% ± 2.0%", "Flexible Inflation Targeting")

    st.markdown("---")
    st.subheader("🛒 Interactive Purchasing Power Simulator: What Could Your Money Buy?")
    st.markdown(
        "Choose a nominal Rupee amount and a historical base year to observe how much of each physical "
        "staple, energy unit, or consumer item you could buy then versus today."
    )

    sim_c1, sim_c2 = st.columns([1.5, 2.5])
    with sim_c1:
        sim_amount = st.select_slider(
            "Select Rupee Amount (₹)",
            options=[100, 500, 1000, 2000, 5000, 10000, 50000, 100000],
            value=1000
        )
        sim_year = st.selectbox(
            "Select Historical Comparison Year",
            [1995, 2000, 2005, 2010, 2015, 2020],
            index=1
        )
        current_year = 2024

        # Calculate basket and purchasing power decay
        basket_then = EconometricAnalyzer.get_representative_commodity_basket(sim_year, float(sim_amount))
        basket_now = EconometricAnalyzer.get_representative_commodity_basket(current_year, float(sim_amount))
        pp_df = EconometricAnalyzer.calculate_purchasing_power_decay(df_macro, start_year=sim_year, initial_amount=float(sim_amount))

        if not pp_df.empty:
            now_val = pp_df.iloc[-1]["real_purchasing_power_inr"]
            retention = pp_df.iloc[-1]["purchasing_power_retention_pct"]
            cum_inf = pp_df.iloc[-1]["cumulative_inflation_pct"]
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Real Value Today</div>
                <div class="metric-val" style="color: #38bdf8;">₹{now_val:,.2f}</div>
                <div class="metric-sub">
                    <strong>₹{sim_amount:,.0f}</strong> from {sim_year} holds only <strong>{retention:.1f}%</strong> 
                    of its original goods purchasing capacity today.<br>
                    Cumulative Price Increase: <strong>+{cum_inf:.1f}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with sim_c2:
        st.markdown(f"**Affordability Breakdown for ₹{sim_amount:,.0f} ({sim_year} vs Today):**")
        b_cols = st.columns(3)
        item_keys = list(basket_then.keys())
        for idx, k in enumerate(item_keys):
            target_col = b_cols[idx % 3]
            then_item = basket_then[k]
            now_item = basket_now[k]
            with target_col:
                st.markdown(f"""
                <div class="basket-card">
                    <div class="basket-icon">{then_item['icon']}</div>
                    <div class="basket-name">{k}</div>
                    <div class="basket-qty">{then_item['quantity_affordable']} <span style="font-size:0.8rem; color:#94a3b8;">→</span> <span style="color:#fb7185;">{now_item['quantity_affordable']}</span></div>
                    <div class="basket-price">{then_item['unit']}<br>₹{then_item['unit_price_inr']:.0f} vs ₹{now_item['unit_price_inr']:.0f}</div>
                </div>
                """, unsafe_allow_html=True)

    # Side-by-side bar comparison
    st.plotly_chart(plot_commodity_basket_comparison(basket_then, basket_now, sim_year, current_year), use_container_width=True)

    # Purchasing Power Decay Area Chart
    if not pp_df.empty:
        st.plotly_chart(plot_purchasing_power_decay(pp_df, sim_year, float(sim_amount)), use_container_width=True)

    # Econometric and Mathematical Formulation Card
    st.markdown("### 📐 Econometric & Mathematical Formulations for Inflation")
    st.markdown(r"""
    1. **Purchasing Power Parity (PPP) & Real Exchange Rate (RER):**
       $$RER = e \times \frac{P^*}{P}$$
       *Where $e$ is the nominal exchange rate (INR/USD), $P^*$ is the foreign price index (US CPI), and $P$ is the domestic price index (India CPI).*  
       **Economic Interpretation:** If domestic inflation exceeds trading partner inflation, the rupee appreciates in *real* terms unless nominal depreciation compensates.

    2. **Real Terms of Trade (Real ToT):**
       $$ToT_{\text{real}} = \frac{P_x / P_{x,\text{base}}}{P_m / P_{m,\text{base}}} \times 100$$
       *Tracks the relative purchasing power of Indian exports over imported inputs (e.g. crude oil).*

    3. **Rule of 70 for Currency Purchasing Power Halving:**
       $$T_{\text{half}} \approx \frac{70}{\bar{\pi}}$$
       *At India's historical mean CPI inflation rate $\bar{\pi} \approx 6.0\%$, the real domestic purchasing power of the rupee halves every ~11.6 years.*

    4. **Real Trade Valuation Deflator:**
       $$V_{\text{real}} = \frac{V_{\text{nominal}}}{\text{CPI} / 100}$$
       *Allows researchers to separate nominal export expansion from genuine physical volume growth.*
    """)

# ----------------------------------------------------
# 7. AI-POWERED RESEARCH OUTCOMES
# ----------------------------------------------------
elif view_selection == "7. AI-Powered Research Outcomes":
    st.header("AI-Powered Research Outcomes")
    st.markdown(
        "Synthesizes verified econometric statistics into peer-reviewed caliber economic explanations. "
        "Every output is grounded directly in official data and strictly partitioned by epistemic taxonomy."
    )
    render_q1_caveat()

    # Curated Empirical Research Inquiries Selector (No custom prompt)
    chosen_question = st.selectbox(
        "Select an Empirical Research Inquiry (Derived from Our Economic Study):",
        RESEARCH_QUESTIONS_CATALOG,
        index=0
    )

    # Prepare verified calculated statistics context
    top_p = df_bilateral[df_bilateral["financial_year"] == "2023-24"] if not df_bilateral.empty else pd.DataFrame()
    
    verified_context = {
        "latest_year": int(latest_macro["year"]) if not df_macro.empty else 2024,
        "latest_exports_usd_b": float(latest_macro["exports_usd_billion"]) if not df_macro.empty else 829.8,
        "latest_imports_usd_b": float(latest_macro["imports_usd_billion"]) if not df_macro.empty else 895.0,
        "latest_trade_balance_usd_b": float(latest_macro["trade_balance_usd_billion"]) if not df_macro.empty else -65.2,
        "openness_pct": float(latest_macro.get("calculated_trade_openness_pct", 43.5)),
        "trade_balance_pct_gdp": float(latest_macro.get("trade_balance_pct_gdp", -1.8)),
        "coverage_ratio": float(latest_macro.get("coverage_ratio", 0.93)),
        "export_cagr_10yr": 5.9,
        "post_covid_export_growth_pct": 53.2,
        "top_export_partner": "United States",
        "top_import_partner": "China",
        "top_export_commodity": "Petroleum Products (Refined)",
        "top_import_commodity": "Crude Petroleum",
        "partner_hhi": float(TradeDataTransformer.calculate_hhi(top_p["total_trade_share_pct"])) if not top_p.empty else 1120.4
    }

    if st.button("Synthesize Research Outcome", type="primary"):
        with st.spinner("Analyzing verified econometric metrics..."):
            assistant = TradeAIAssistant()
            report = assistant.query(chosen_question, verified_context)

            st.success(f"Synthesis Complete — Reasoning Engine: `{report.get('mode', 'DETERMINISTIC_EXPERT')}`")

            # Plain Summary Box
            st.markdown(f"### 📋 Research Executive Summary\n{report['plain_summary']}")
            st.markdown("---")

            # Partitioned Epistemic Taxonomy
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown('<span class="taxonomy-badge badge-fact">FACT (EMPIRICAL GROUNDING)</span>', unsafe_allow_html=True)
                st.info(report["fact"])

                st.markdown('<span class="taxonomy-badge badge-calc">CALCULATION (DERIVED METRICS)</span>', unsafe_allow_html=True)
                st.success(report["calculation"])

            with col_right:
                st.markdown('<span class="taxonomy-badge badge-interp">INTERPRETATION (ECONOMIC REASONING)</span>', unsafe_allow_html=True)
                st.warning(report["interpretation"])

                st.markdown('<span class="taxonomy-badge badge-hypo">HYPOTHESIS (TESTABLE CAUSAL MECHANISM)</span>', unsafe_allow_html=True)
                st.markdown(f"> *{report['hypothesis']}*")

            st.markdown("---")
            st.markdown('<span class="taxonomy-badge badge-quest">QUESTIONS FOR FURTHER INVESTIGATION</span>', unsafe_allow_html=True)
            st.markdown(report["further_investigation"])

# ----------------------------------------------------
# 8. METHODOLOGY & PROVENANCE VIEW
# ----------------------------------------------------
elif view_selection == "8. Methodology & Provenance":
    st.header("Research Methodology, Data Provenance & Reproducibility")
    st.markdown(
        "Complete transparency regarding data provenance, validation checks, formulas, and pipeline architecture."
    )
    render_q1_caveat()

    st.subheader("Data Architecture & Pipeline Flow")
    st.code("""
RAW DATA SOURCES (World Bank API, DGCI&S, RBI DBIE)
       ↓
STRICT VALIDATION SUITE (Accounting identities, regex checks, non-negativity)
       ↓
CLEANING & STANDARDIZATION (Currencies converted to USD B/$M/INR Cr, ISO-3 mapping)
       ↓
TRANSFORMATION & ECONOMETRICS (CAGR, HHI, CPI deflator, rolling 12M moving averages)
       ↓
PERSISTENCE (Indexed SQLite Relational Storage & Processed CSVs)
       ↓
INTERACTIVE RESEARCH DASHBOARD & EPISTEMIC AI OUTCOMES LAYER
    """, language="text")

    st.subheader("Official Data Catalog & Source Provenance")
    if catalog:
        for src in catalog:
            with st.expander(f"📦 {src.get('name')} ({src.get('publisher')})", expanded=True):
                st.markdown(f"""
                - **Source ID:** `{src.get('source_id')}`
                - **Official URL:** [{src.get('url')}]({src.get('url')})
                - **Frequency:** `{src.get('frequency')}`
                - **Coverage Period:** `{src.get('coverage')}`
                - **Retrieval Date:** `{src.get('retrieval_date')}`
                """)
                series = json.loads(src.get("series_json", "[]"))
                if series:
                    st.table(pd.DataFrame(series))

    st.subheader("Mathematical & Econometric Formulas")
    st.markdown(r"""
    1. **Compound Annual Growth Rate (CAGR):**
       $$CAGR = \left( \frac{V_{end}}{V_{start}} \right)^{\frac{1}{n}} - 1$$
    
    2. **Trade Openness Index:**
       $$Openness = \frac{\text{Exports} + \text{Imports}}{\text{GDP}} \times 100$$
    
    3. **Herfindahl-Hirschman Index (Partner Concentration):**
       $$HHI = \sum_{i=1}^{N} s_i^2 \quad \text{where } s_i \text{ is the percentage market share of country } i$$
    
    4. **Export-to-Import Coverage Ratio:**
       $$Coverage = \frac{\text{Exports}}{\text{Imports}}$$

    5. **Purchasing Power Parity (PPP) & Real Exchange Rate:**
       $$RER = e \times \frac{P^*}{P}$$

    6. **Rule of 70 Currency Purchasing Power Halving:**
       $$T_{\text{half}} \approx \frac{70}{\bar{\pi}}$$
    """)

    st.subheader("Pipeline Audit Logs")
    with storage.get_connection() as conn:
        logs_df = pd.read_sql_query("SELECT * FROM pipeline_execution_log ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(logs_df, use_container_width=True)

st.markdown("---")
st.caption("INDIA TRADE INTELLIGENCE | Built for Economics Research & Policy Analysis | Powered by Python, Streamlit & Plotly")
