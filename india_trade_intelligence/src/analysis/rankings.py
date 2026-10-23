"""Rankings, partner concentration, and commodity driver analysis."""
import pandas as pd
from typing import Dict, Any, List

class TradeRankingsAnalyzer:
    """Computes country and commodity leaderboards, surpluses, and deficits."""

    @staticmethod
    def get_top_partners(df_bilateral: pd.DataFrame, financial_year: str, n: int = 10) -> Dict[str, pd.DataFrame]:
        """Returns top export destinations, top import sources, and bilateral balance leaders."""
        df_year = df_bilateral[df_bilateral["financial_year"] == financial_year].copy()
        if df_year.empty:
            return {}

        top_exports = df_year.sort_values("exports_usd_million", ascending=False).head(n)[
            ["country", "iso3", "region", "exports_usd_million", "export_share_pct", "export_rank"]
        ]

        top_imports = df_year.sort_values("imports_usd_million", ascending=False).head(n)[
            ["country", "iso3", "region", "imports_usd_million", "import_share_pct", "import_rank"]
        ]

        top_surplus = df_year.sort_values("trade_balance_usd_million", ascending=False).head(n)[
            ["country", "iso3", "region", "exports_usd_million", "imports_usd_million", "trade_balance_usd_million"]
        ]

        top_deficit = df_year.sort_values("trade_balance_usd_million", ascending=True).head(n)[
            ["country", "iso3", "region", "exports_usd_million", "imports_usd_million", "trade_balance_usd_million"]
        ]

        return {
            "top_exports": top_exports,
            "top_imports": top_imports,
            "top_surplus": top_surplus,
            "top_deficit": top_deficit
        }

    @staticmethod
    def get_regional_breakdown(df_bilateral: pd.DataFrame, financial_year: str) -> pd.DataFrame:
        """Aggregates trade volumes and balances by geographic region."""
        df_year = df_bilateral[df_bilateral["financial_year"] == financial_year].copy()
        if df_year.empty or "region" not in df_year.columns:
            return pd.DataFrame()

        regional = df_year.groupby("region").agg(
            total_exports_usd_m=("exports_usd_million", "sum"),
            total_imports_usd_m=("imports_usd_million", "sum"),
            net_balance_usd_m=("trade_balance_usd_million", "sum"),
            total_trade_usd_m=("total_trade_usd_million", "sum")
        ).reset_index()

        tot = regional["total_trade_usd_m"].sum()
        if tot > 0:
            regional["regional_share_pct"] = ((regional["total_trade_usd_m"] / tot) * 100.0).round(2)
        
        return regional.sort_values("total_trade_usd_m", ascending=False).reset_index(drop=True)

    @staticmethod
    def get_top_commodities(df_commodity: pd.DataFrame, financial_year: str, flow: str = "Export", n: int = 10) -> pd.DataFrame:
        """Returns top commodities for a specified trade flow and financial year."""
        filtered = df_commodity[
            (df_commodity["financial_year"] == financial_year) &
            (df_commodity["trade_flow"] == flow)
        ].copy()
        
        return filtered.sort_values("value_usd_million", ascending=False).head(n)[
            ["commodity_group", "sector_category", "value_usd_million", "value_usd_billion", "commodity_share_pct", "description_notes"]
        ].reset_index(drop=True)
