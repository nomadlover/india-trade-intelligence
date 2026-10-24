"""Analytical transformation and econometric calculations module.
Computes growth rates, CAGR, trade openness, HHI concentration, coverage ratios,
and rolling statistical momentum.
"""
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List

class TradeDataTransformer:
    """Executes verified mathematical and econometric transformations."""

    @staticmethod
    def calculate_cagr(start_val: float, end_val: float, num_periods: int) -> Optional[float]:
        """Calculates Compound Annual Growth Rate (CAGR) in percent.
        
        Formula: ((end_val / start_val) ** (1 / num_periods) - 1) * 100
        Returns None if start_val <= 0, end_val <= 0, or num_periods <= 0.
        """
        if start_val <= 0 or end_val <= 0 or num_periods <= 0:
            return None
        cagr = ((end_val / start_val) ** (1.0 / num_periods) - 1.0) * 100.0
        return round(float(cagr), 2)

    @staticmethod
    def calculate_yoy_growth(series: pd.Series) -> pd.Series:
        """Calculates year-over-year percentage growth rate."""
        return (series.pct_change() * 100.0).round(2)

    @staticmethod
    def calculate_hhi(shares_pct: pd.Series) -> float:
        """Calculates the Herfindahl-Hirschman Index (HHI) of market concentration.
        
        Formula: Sum of squared percentage shares (e.g. 20% -> 400).
        Range: 0 to 10,000.
        Economic interpretation:
          - HHI < 1,500: Diversified / Unconcentrated
          - 1,500 <= HHI <= 2,500: Moderately Concentrated
          - HHI > 2,500: Highly Concentrated
        """
        clean_shares = shares_pct.dropna()
        if clean_shares.empty:
            return 0.0
        # Normalize to 100% if shares represent a subset
        total = clean_shares.sum()
        if total > 0:
            normalized_pct = (clean_shares / total) * 100.0
            hhi = (normalized_pct ** 2).sum()
            return round(float(hhi), 2)
        return 0.0

    @classmethod
    def transform_macro_annual(cls, df_macro: pd.DataFrame) -> pd.DataFrame:
        """Enriches macro annual data with growth rates, GDP shares, and coverage ratios."""
        df = df_macro.copy().sort_values("year").reset_index(drop=True)

        # YoY Growth rates
        if "exports_usd_billion" in df.columns:
            df["exports_yoy_pct"] = cls.calculate_yoy_growth(df["exports_usd_billion"])
        if "imports_usd_billion" in df.columns:
            df["imports_yoy_pct"] = cls.calculate_yoy_growth(df["imports_usd_billion"])
        if "gdp_usd_billion" in df.columns:
            df["gdp_yoy_pct"] = cls.calculate_yoy_growth(df["gdp_usd_billion"])

        # Openness & GDP Ratios
        if "gdp_usd_billion" in df.columns and "exports_usd_billion" in df.columns:
            df["exports_pct_gdp"] = ((df["exports_usd_billion"] / df["gdp_usd_billion"]) * 100.0).round(2)
            df["imports_pct_gdp"] = ((df["imports_usd_billion"] / df["gdp_usd_billion"]) * 100.0).round(2)
            df["calculated_trade_openness_pct"] = (
                ((df["exports_usd_billion"] + df["imports_usd_billion"]) / df["gdp_usd_billion"]) * 100.0
            ).round(2)
            df["trade_balance_pct_gdp"] = (
                ((df["exports_usd_billion"] - df["imports_usd_billion"]) / df["gdp_usd_billion"]) * 100.0
            ).round(2)

        # Export-to-Import Coverage Ratio
        if "exports_usd_billion" in df.columns and "imports_usd_billion" in df.columns:
            df["coverage_ratio"] = (df["exports_usd_billion"] / df["imports_usd_billion"]).round(3)

        return df

    @classmethod
    def transform_bilateral_trade(cls, df_bilateral: pd.DataFrame) -> pd.DataFrame:
        """Enriches bilateral trade with country market shares and partner rankings."""
        df = df_bilateral.copy()

        # Compute annual national totals to derive accurate market shares per financial year
        annual_totals = df.groupby("financial_year").agg(
            annual_tot_exp=("exports_usd_million", "sum"),
            annual_tot_imp=("imports_usd_million", "sum"),
            annual_tot_trade=("total_trade_usd_million", "sum")
        ).reset_index()

        df = df.merge(annual_totals, on="financial_year", how="left")

        df["export_share_pct"] = ((df["exports_usd_million"] / df["annual_tot_exp"]) * 100.0).round(2)
        df["import_share_pct"] = ((df["imports_usd_million"] / df["annual_tot_imp"]) * 100.0).round(2)
        df["total_trade_share_pct"] = ((df["total_trade_usd_million"] / df["annual_tot_trade"]) * 100.0).round(2)

        # Partner rankings per year
        df["export_rank"] = df.groupby("financial_year")["exports_usd_million"].rank(ascending=False, method="min").astype(int)
        df["import_rank"] = df.groupby("financial_year")["imports_usd_million"].rank(ascending=False, method="min").astype(int)
        df["total_trade_rank"] = df.groupby("financial_year")["total_trade_usd_million"].rank(ascending=False, method="min").astype(int)

        # Trade balance status
        df["balance_status"] = np.where(df["trade_balance_usd_million"] >= 0, "Trade Surplus", "Trade Deficit")

        # Bilateral coverage ratio
        df["bilateral_coverage_ratio"] = np.where(
            df["imports_usd_million"] > 0,
            (df["exports_usd_million"] / df["imports_usd_million"]).round(3),
            np.nan
        )

        return df

    @classmethod
    def transform_commodity_trade(cls, df_commodity: pd.DataFrame) -> pd.DataFrame:
        """Enriches commodity data with category shares, rankings, and composition shifts."""
        df = df_commodity.copy()

        # Group totals per FY and trade flow
        flow_totals = df.groupby(["financial_year", "trade_flow"])["value_usd_million"].sum().reset_index()
        flow_totals = flow_totals.rename(columns={"value_usd_million": "flow_total_usd_million"})

        df = df.merge(flow_totals, on=["financial_year", "trade_flow"], how="left")
        df["commodity_share_pct"] = ((df["value_usd_million"] / df["flow_total_usd_million"]) * 100.0).round(2)
        df["rank_in_flow"] = df.groupby(["financial_year", "trade_flow"])["value_usd_million"].rank(
            ascending=False, method="min"
        ).astype(int)

        return df

    @classmethod
    def transform_monthly_trade(cls, df_monthly: pd.DataFrame) -> pd.DataFrame:
        """Enriches monthly trade series with rolling moving averages and volatility."""
        df = df_monthly.copy().sort_values("date").reset_index(drop=True)

        # Rolling Moving Averages (3-month & 12-month smoothing)
        df["exports_3m_ma"] = df["merchandise_exports_usd_million"].rolling(window=3, min_periods=1).mean().round(2)
        df["imports_3m_ma"] = df["merchandise_imports_usd_million"].rolling(window=3, min_periods=1).mean().round(2)
        df["deficit_3m_ma"] = df["merchandise_trade_balance_usd_million"].rolling(window=3, min_periods=1).mean().round(2)

        df["exports_12m_ma"] = df["merchandise_exports_usd_million"].rolling(window=12, min_periods=1).mean().round(2)
        df["imports_12m_ma"] = df["merchandise_imports_usd_million"].rolling(window=12, min_periods=1).mean().round(2)
        df["deficit_12m_ma"] = df["merchandise_trade_balance_usd_million"].rolling(window=12, min_periods=1).mean().round(2)

        # Non-Oil merchandise trade balance
        df["non_oil_trade_balance_usd_million"] = (
            df["non_oil_exports_usd_million"] - df["non_oil_imports_usd_million"]
        ).round(2)

        # Rolling Deficit Volatility (6-month standard deviation)
        df["deficit_volatility_6m"] = df["merchandise_trade_balance_usd_million"].rolling(window=6, min_periods=2).std().round(2)

        # YoY growth at monthly frequency (12-period lag)
        df["exports_yoy_pct"] = (df["merchandise_exports_usd_million"].pct_change(periods=12) * 100.0).round(2)
        df["imports_yoy_pct"] = (df["merchandise_imports_usd_million"].pct_change(periods=12) * 100.0).round(2)

        return df

    @classmethod
    def combine_merchandise_and_services(
        cls,
        df_merchandise: pd.DataFrame,
        df_services: pd.DataFrame,
        period_col: str = "period"
    ) -> pd.DataFrame:
        """Transparently combines merchandise and services series into aggregate trade flows.
        
        Strictly enforces:
        1. Accounting Identities:
           Total Exports = Merchandise Exports + Services Exports
           Total Imports = Merchandise Imports + Services Imports
           Total Trade Balance = Total Exports - Total Imports
        2. Status Propagation:
           Inherits the lowest data status among components. If merchandise is PROVISIONAL
           or services is ESTIMATED, the combined total is marked as PROVISIONAL_AND_ESTIMATED.
        """
        if df_merchandise.empty or df_services.empty:
            return pd.DataFrame()

        m_df = df_merchandise.copy()
        s_df = df_services.copy()

        # Support flexible column aliases
        for target, aliases in [
            ("merchandise_exports_usd_billion", ["merchandise_exports_usd_billion", "merchandise_exports", "exports_usd_billion", "exports"]),
            ("merchandise_imports_usd_billion", ["merchandise_imports_usd_billion", "merchandise_imports", "imports_usd_billion", "imports"]),
            ("merchandise_status", ["merchandise_status", "publication_status", "status"])
        ]:
            if target not in m_df.columns:
                for a in aliases:
                    if a in m_df.columns:
                        m_df[target] = m_df[a]
                        break

        for target, aliases in [
            ("services_exports_usd_billion", ["services_exports_usd_billion", "services_exports", "exports_usd_billion", "exports"]),
            ("services_imports_usd_billion", ["services_imports_usd_billion", "services_imports", "imports_usd_billion", "imports"]),
            ("services_status", ["services_status", "publication_status", "status"])
        ]:
            if target not in s_df.columns:
                for a in aliases:
                    if a in s_df.columns:
                        s_df[target] = s_df[a]
                        break

        merged = pd.merge(m_df, s_df, on=period_col, how="outer", suffixes=("_merch_orig", "_serv_orig"))
        if merged.empty:
            return pd.DataFrame()

        if "merchandise_exports_usd_billion" in merged.columns and "services_exports_usd_billion" in merged.columns:
            has_both_exp = merged["merchandise_exports_usd_billion"].notna() & merged["services_exports_usd_billion"].notna()
            merged["total_exports_usd_billion"] = np.where(
                has_both_exp,
                np.round(merged["merchandise_exports_usd_billion"] + merged["services_exports_usd_billion"], 2),
                np.nan
            )
        else:
            merged["total_exports_usd_billion"] = np.nan

        if "merchandise_imports_usd_billion" in merged.columns and "services_imports_usd_billion" in merged.columns:
            has_both_imp = merged["merchandise_imports_usd_billion"].notna() & merged["services_imports_usd_billion"].notna()
            merged["total_imports_usd_billion"] = np.where(
                has_both_imp,
                np.round(merged["merchandise_imports_usd_billion"] + merged["services_imports_usd_billion"], 2),
                np.nan
            )
        else:
            merged["total_imports_usd_billion"] = np.nan

        merged["total_trade_balance_usd_billion"] = np.where(
            merged["total_exports_usd_billion"].notna() & merged["total_imports_usd_billion"].notna(),
            (merged["total_exports_usd_billion"] - merged["total_imports_usd_billion"]).round(2),
            np.nan
        )

        if "merchandise_exports_usd_billion" in merged.columns:
            merged["merchandise_share_of_exports_pct"] = np.where(
                merged["total_exports_usd_billion"].notna() & (merged["total_exports_usd_billion"] > 0),
                ((merged["merchandise_exports_usd_billion"] / merged["total_exports_usd_billion"]) * 100.0).round(2),
                np.nan
            )
        if "services_exports_usd_billion" in merged.columns:
            merged["services_share_of_exports_pct"] = np.where(
                merged["total_exports_usd_billion"].notna() & (merged["total_exports_usd_billion"] > 0),
                ((merged["services_exports_usd_billion"] / merged["total_exports_usd_billion"]) * 100.0).round(2),
                np.nan
            )

        # Propagate status
        def get_composite_status(row):
            m_val = row.get("merchandise_exports_usd_billion")
            s_val = row.get("services_exports_usd_billion")
            if pd.isna(m_val) or pd.isna(s_val):
                return "PERIOD_MISMATCH_OR_UNKNOWN"
            m_stat = row.get("merchandise_status", "FINAL")
            s_stat = row.get("services_status", "FINAL")
            if "PROVISIONAL" in str(m_stat) or "PROVISIONAL" in str(s_stat):
                return "PROVISIONAL_COMPOSITE"
            if "ESTIMATED" in str(m_stat) or "ESTIMATED" in str(s_stat):
                return "ESTIMATED_COMPOSITE"
            return "FINAL_RECONCILED"

        merged["composite_data_status"] = merged.apply(get_composite_status, axis=1)
        return merged
