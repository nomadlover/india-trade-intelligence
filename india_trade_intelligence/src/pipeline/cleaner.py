"""Data cleaning and standardization module for India Trade Intelligence.
Standardizes schemas, currencies, country ISO codes, and temporal indices.
"""
import logging
import pandas as pd
from typing import Dict, Any, Tuple
from pathlib import Path

from india_trade_intelligence.src.config import (
    COUNTRY_ISO_MAP,
    PROCESSED_DATA_DIR
)

logger = logging.getLogger(__name__)

class TradeDataCleaner:
    """Standardizes raw trade datasets into clean analytical structures."""

    def __init__(self, processed_dir: Path = PROCESSED_DATA_DIR):
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def clean_world_bank_payload(self, payload: Dict[str, Any]) -> pd.DataFrame:
        """Flattens World Bank multi-indicator JSON payload into a clean annual time-series dataframe."""
        indicators_data = payload.get("indicators", {})
        
        # Collect all observations by year
        records_by_year: Dict[int, Dict[str, Any]] = {}
        
        for ind_key, content in indicators_data.items():
            records = content.get("records", [])
            for r in records:
                date_str = r.get("date")
                val = r.get("value")
                if date_str is None or not str(date_str).isdigit():
                    continue
                year = int(date_str)
                if year not in records_by_year:
                    records_by_year[year] = {"year": year}
                
                # Assign value
                records_by_year[year][ind_key] = val

        df = pd.DataFrame(list(records_by_year.values()))
        if df.empty:
            raise ValueError("Processed World Bank dataframe is empty.")

        # Sort chronologically
        df = df.sort_values("year").reset_index(drop=True)
        
        # Standardize units: convert raw USD to USD Billions for readability and numerical stability
        if "exports_gnfs" in df.columns:
            df["exports_usd_billion"] = df["exports_gnfs"] / 1e9
        if "imports_gnfs" in df.columns:
            df["imports_usd_billion"] = df["imports_gnfs"] / 1e9
        if "gdp_current_usd" in df.columns:
            df["gdp_usd_billion"] = df["gdp_current_usd"] / 1e9
        if "merchandise_exports" in df.columns:
            df["merchandise_exports_usd_billion"] = df["merchandise_exports"] / 1e9
        if "merchandise_imports" in df.columns:
            df["merchandise_imports_usd_billion"] = df["merchandise_imports"] / 1e9

        # Fill trade balance: Exports - Imports
        if "exports_usd_billion" in df.columns and "imports_usd_billion" in df.columns:
            df["trade_balance_usd_billion"] = df["exports_usd_billion"] - df["imports_usd_billion"]
            df["total_trade_usd_billion"] = df["exports_usd_billion"] + df["imports_usd_billion"]

        # Ensure macro columns exist with clean names
        col_rename = {
            "exchange_rate_inr_usd": "exchange_rate_inr_per_usd",
            "inflation_cpi_pct": "cpi_inflation_pct",
            "trade_pct_gdp": "trade_openness_official_pct"
        }
        df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})

        # Save processed
        output_path = self.processed_dir / "macro_annual_cleaned.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned macro annual data to {output_path}")
        return df

    def clean_bilateral_trade(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Cleans and standardizes bilateral partner trade data."""
        df = df_raw.copy()
        
        # Map ISO-3 country codes
        df["iso3"] = df["country"].map(COUNTRY_ISO_MAP).fillna("OTH")
        
        # Extract financial year start and end calendar years
        # e.g., '2023-24' -> start 2023, end 2024
        df["fy_start_year"] = df["financial_year"].apply(lambda x: int(x.split("-")[0]))
        df["fy_end_year"] = df["fy_start_year"] + 1

        # Standardize currency units into both USD Billion and USD Million
        df["exports_usd_billion"] = df["exports_usd_million"] / 1000.0
        df["imports_usd_billion"] = df["imports_usd_million"] / 1000.0
        df["trade_balance_usd_billion"] = df["trade_balance_usd_million"] / 1000.0
        df["total_trade_usd_billion"] = df["total_trade_usd_million"] / 1000.0

        # Sort by financial year and total trade descending
        df = df.sort_values(by=["financial_year", "total_trade_usd_million"], ascending=[True, False]).reset_index(drop=True)

        output_path = self.processed_dir / "bilateral_trade_cleaned.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned bilateral trade to {output_path}")
        return df

    def clean_commodity_trade(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Cleans and standardizes commodity sectors dataset."""
        df = df_raw.copy()
        df["fy_start_year"] = df["financial_year"].apply(lambda x: int(x.split("-")[0]))
        df["fy_end_year"] = df["fy_start_year"] + 1
        
        # Convert values to USD Billion
        df["value_usd_billion"] = df["value_usd_million"] / 1000.0

        df = df.sort_values(by=["financial_year", "trade_flow", "value_usd_million"], ascending=[True, True, False]).reset_index(drop=True)

        output_path = self.processed_dir / "commodity_trade_cleaned.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned commodity trade to {output_path}")
        return df

    def clean_monthly_trade(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Cleans and creates continuous monthly datetime index."""
        df = df_raw.copy()
        df["date"] = pd.to_datetime(df["period"] + "-01")
        
        # Convert to USD Billion
        df["merchandise_exports_usd_billion"] = df["merchandise_exports_usd_million"] / 1000.0
        df["merchandise_imports_usd_billion"] = df["merchandise_imports_usd_million"] / 1000.0
        df["merchandise_trade_balance_usd_billion"] = df["merchandise_trade_balance_usd_million"] / 1000.0
        
        df = df.sort_values("date").reset_index(drop=True)

        output_path = self.processed_dir / "monthly_trade_cleaned.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned monthly trade to {output_path}")
        return df
