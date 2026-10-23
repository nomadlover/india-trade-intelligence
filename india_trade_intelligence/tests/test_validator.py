"""Tests for data validation logic, accounting identities, and schema checks."""
import pytest
import pandas as pd
from india_trade_intelligence.src.pipeline.validator import TradeDataValidator

def test_validate_bilateral_trade_valid():
    df = pd.DataFrame([{
        "financial_year": "2023-24",
        "country": "United States",
        "exports_usd_million": 77500.0,
        "imports_usd_million": 42500.0,
        "trade_balance_usd_million": 35000.0,
        "total_trade_usd_million": 120000.0
    }])
    report = TradeDataValidator.validate_bilateral_trade(df)
    assert report.is_valid is True
    assert len(report.failed_checks) == 0

def test_validate_bilateral_trade_identity_violation():
    # Trade balance does not equal exports - imports
    df = pd.DataFrame([{
        "financial_year": "2023-24",
        "country": "United States",
        "exports_usd_million": 77500.0,
        "imports_usd_million": 42500.0,
        "trade_balance_usd_million": 99999.0, # Grossly wrong
        "total_trade_usd_million": 120000.0
    }])
    report = TradeDataValidator.validate_bilateral_trade(df)
    assert report.is_valid is False
    assert any("Accounting identity violation" in f for f in report.failed_checks)

def test_validate_bilateral_trade_negative_values():
    df = pd.DataFrame([{
        "financial_year": "2023-24",
        "country": "United States",
        "exports_usd_million": -500.0, # Negative export impossible
        "imports_usd_million": 42500.0,
        "trade_balance_usd_million": -43000.0,
        "total_trade_usd_million": 42000.0
    }])
    report = TradeDataValidator.validate_bilateral_trade(df)
    assert report.is_valid is False
    assert any("Negative exports found" in f for f in report.failed_checks)

def test_validate_bilateral_trade_invalid_fy_format():
    df = pd.DataFrame([{
        "financial_year": "2023/2024", # Invalid slash format instead of YYYY-YY
        "country": "United States",
        "exports_usd_million": 77500.0,
        "imports_usd_million": 42500.0,
        "trade_balance_usd_million": 35000.0,
        "total_trade_usd_million": 120000.0
    }])
    report = TradeDataValidator.validate_bilateral_trade(df)
    assert report.is_valid is False
    assert any("invalid FY format" in f for f in report.failed_checks)

def test_validate_commodity_trade_valid():
    df = pd.DataFrame([{
        "financial_year": "2023-24",
        "commodity_group": "Electronic Goods (incl. Smartphones)",
        "trade_flow": "Export",
        "value_usd_million": 29120.0
    }])
    report = TradeDataValidator.validate_commodity_trade(df)
    assert report.is_valid is True

def test_validate_commodity_trade_invalid_flow():
    df = pd.DataFrame([{
        "financial_year": "2023-24",
        "commodity_group": "Electronic Goods (incl. Smartphones)",
        "trade_flow": "ReExportInvalid",
        "value_usd_million": 29120.0
    }])
    report = TradeDataValidator.validate_commodity_trade(df)
    assert report.is_valid is False
    assert any("Invalid trade flow" in f for f in report.failed_checks)

def test_validate_monthly_trade_period_regex():
    df = pd.DataFrame([{
        "period": "2024-15", # Month 15 does not exist
        "year": 2024,
        "month": 15,
        "merchandise_exports_usd_million": 35000.0,
        "merchandise_imports_usd_million": 50000.0,
        "merchandise_trade_balance_usd_million": -15000.0
    }])
    report = TradeDataValidator.validate_monthly_trade(df)
    assert report.is_valid is False
    assert any("Invalid period format" in f for f in report.failed_checks)
