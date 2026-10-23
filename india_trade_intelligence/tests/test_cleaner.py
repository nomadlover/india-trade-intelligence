"""Tests for data cleaning, currency conversions, and country mapping."""
import pandas as pd
from india_trade_intelligence.src.pipeline.cleaner import TradeDataCleaner
from india_trade_intelligence.src.config import COUNTRY_ISO_MAP

def test_clean_bilateral_trade_currency_conversion():
    cleaner = TradeDataCleaner()
    df_raw = pd.DataFrame([{
        "financial_year": "2023-24",
        "country": "United States",
        "region": "North America",
        "exports_usd_million": 77500.0,
        "imports_usd_million": 42500.0,
        "trade_balance_usd_million": 35000.0,
        "total_trade_usd_million": 120000.0,
        "exports_inr_crore": 643250.0,
        "imports_inr_crore": 352750.0,
        "trade_balance_inr_crore": 290500.0,
        "data_source": "DGCI&S",
        "source_url": "https://tradestat.commerce.gov.in/eidb/"
    }])

    df_clean = cleaner.clean_bilateral_trade(df_raw)

    # Unit conversions: $77,500 Million -> $77.50 Billion
    assert round(df_clean.loc[0, "exports_usd_billion"], 2) == 77.50
    assert round(df_clean.loc[0, "imports_usd_billion"], 2) == 42.50
    assert round(df_clean.loc[0, "trade_balance_usd_billion"], 2) == 35.00
    assert round(df_clean.loc[0, "total_trade_usd_billion"], 2) == 120.00

def test_clean_bilateral_trade_iso_country_mapping():
    cleaner = TradeDataCleaner()
    df_raw = pd.DataFrame([
        {
            "financial_year": "2023-24",
            "country": "United States",
            "exports_usd_million": 100.0, "imports_usd_million": 50.0,
            "trade_balance_usd_million": 50.0, "total_trade_usd_million": 150.0
        },
        {
            "financial_year": "2023-24",
            "country": "China",
            "exports_usd_million": 10.0, "imports_usd_million": 80.0,
            "trade_balance_usd_million": -70.0, "total_trade_usd_million": 90.0
        }
    ])
    df_clean = cleaner.clean_bilateral_trade(df_raw)
    assert df_clean.loc[df_clean["country"] == "United States", "iso3"].iloc[0] == "USA"
    assert df_clean.loc[df_clean["country"] == "China", "iso3"].iloc[0] == "CHN"

def test_clean_commodity_trade():
    cleaner = TradeDataCleaner()
    df_raw = pd.DataFrame([{
        "financial_year": "2023-24",
        "commodity_group": "Electronic Goods (incl. Smartphones)",
        "trade_flow": "Export",
        "sector_category": "Manufacturing",
        "value_usd_million": 29120.0,
        "value_inr_crore": 241696.0,
        "description_notes": "Smartphones",
        "data_source": "DGCI&S",
        "source_url": "https://tradestat.commerce.gov.in/eidb/"
    }])

    df_clean = cleaner.clean_commodity_trade(df_raw)
    assert df_clean.loc[0, "fy_start_year"] == 2023
    assert df_clean.loc[0, "fy_end_year"] == 2024
    assert round(df_clean.loc[0, "value_usd_billion"], 2) == 29.12

def test_clean_monthly_trade_date_parsing():
    cleaner = TradeDataCleaner()
    df_raw = pd.DataFrame([{
        "period": "2024-04",
        "year": 2024,
        "month": 4,
        "merchandise_exports_usd_million": 34990.0,
        "merchandise_imports_usd_million": 54090.0,
        "merchandise_trade_balance_usd_million": -19100.0,
        "oil_imports_usd_million": 15000.0,
        "non_oil_imports_usd_million": 39090.0,
        "non_oil_exports_usd_million": 28690.0,
        "data_source": "RBI",
        "source_url": "https://data.rbi.org.in/"
    }])

    df_clean = cleaner.clean_monthly_trade(df_raw)
    assert df_clean.loc[0, "date"].year == 2024
    assert df_clean.loc[0, "date"].month == 4
    assert round(df_clean.loc[0, "merchandise_exports_usd_billion"], 2) == 34.99
