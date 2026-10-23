"""Tests for analytical transformations: CAGR, HHI, YoY growth, trade balance and openness."""
import pytest
import pandas as pd
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer

def test_cagr_calculation():
    # Value doubles from 100 to 200 in 7.27 years (~10% CAGR)
    # Exactly: 100 to 121 in 2 years is 10.0%
    cagr = TradeDataTransformer.calculate_cagr(100.0, 121.0, 2)
    assert cagr == 10.0

    # Negative / zero checks
    assert TradeDataTransformer.calculate_cagr(-50, 100, 3) is None
    assert TradeDataTransformer.calculate_cagr(100, -50, 3) is None
    assert TradeDataTransformer.calculate_cagr(100, 200, 0) is None

def test_yoy_growth():
    s = pd.Series([100.0, 120.0, 150.0])
    yoy = TradeDataTransformer.calculate_yoy_growth(s)
    assert pd.isna(yoy.iloc[0])
    assert yoy.iloc[1] == 20.0
    assert yoy.iloc[2] == 25.0

def test_hhi_concentration():
    # 4 equal firms/countries each 25% share: 4 * (25^2) = 2500
    shares = pd.Series([25.0, 25.0, 25.0, 25.0])
    hhi = TradeDataTransformer.calculate_hhi(shares)
    assert hhi == 2500.0

    # Complete monopoly: 1 country 100% share: 1 * (100^2) = 10000
    mono = pd.Series([100.0])
    assert TradeDataTransformer.calculate_hhi(mono) == 10000.0

    # Highly diversified: 10 equal partners (10% each): 10 * (10^2) = 1000 (< 1500 unconcentrated)
    div = pd.Series([10.0] * 10)
    assert TradeDataTransformer.calculate_hhi(div) == 1000.0

def test_transform_macro_annual():
    df = pd.DataFrame([
        {"year": 2022, "exports_usd_billion": 500.0, "imports_usd_billion": 600.0, "gdp_usd_billion": 3000.0},
        {"year": 2023, "exports_usd_billion": 550.0, "imports_usd_billion": 660.0, "gdp_usd_billion": 3300.0}
    ])
    res = TradeDataTransformer.transform_macro_annual(df)
    
    # 500 to 550 is 10.0% YoY
    assert res.loc[1, "exports_yoy_pct"] == 10.0
    # Openness: (550 + 660) / 3300 = 1210 / 3300 * 100 = 36.67%
    assert round(res.loc[1, "calculated_trade_openness_pct"], 1) == 36.7
    # Coverage ratio: 550 / 660 = 0.833
    assert res.loc[1, "coverage_ratio"] == 0.833

def test_transform_bilateral_rankings():
    df = pd.DataFrame([
        {"financial_year": "2023-24", "country": "USA", "exports_usd_million": 70000.0, "imports_usd_million": 40000.0, "total_trade_usd_million": 110000.0, "trade_balance_usd_million": 30000.0},
        {"financial_year": "2023-24", "country": "China", "exports_usd_million": 15000.0, "imports_usd_million": 90000.0, "total_trade_usd_million": 105000.0, "trade_balance_usd_million": -75000.0}
    ])
    res = TradeDataTransformer.transform_bilateral_trade(df)
    usa_row = res[res["country"] == "USA"].iloc[0]
    chn_row = res[res["country"] == "China"].iloc[0]
    
    assert usa_row["export_rank"] == 1
    assert chn_row["import_rank"] == 1
    assert usa_row["balance_status"] == "Trade Surplus"
    assert chn_row["balance_status"] == "Trade Deficit"
