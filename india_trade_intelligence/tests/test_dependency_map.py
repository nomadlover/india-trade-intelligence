"""Automated test suite for Module A: India Trade Dependency Map and Economic Data Contract."""
import pytest
import pandas as pd
import numpy as np

from india_trade_intelligence.src.analysis.contracts import (
    EconomicDataContract,
    ReportingPeriodType,
    CurrencyUnit
)
from india_trade_intelligence.src.analysis.dependency import TradeDependencyAnalyzer


class TestEconomicDataContract:
    """Verifies strict reporting period isolation, safe math, and currency conversions."""

    def test_period_detection(self):
        """Validates detection of Financial Year, Calendar Year, and Monthly periods."""
        assert EconomicDataContract.detect_period_type("2023-24") == ReportingPeriodType.FINANCIAL_YEAR
        assert EconomicDataContract.detect_period_type("FY24") == ReportingPeriodType.FINANCIAL_YEAR
        assert EconomicDataContract.detect_period_type("2023") == ReportingPeriodType.CALENDAR_YEAR
        assert EconomicDataContract.detect_period_type(2023) == ReportingPeriodType.CALENDAR_YEAR
        assert EconomicDataContract.detect_period_type("2024-04") == ReportingPeriodType.MONTHLY

    def test_assert_no_mixed_periods_success(self):
        """Passes when all periods are pure Financial Years."""
        fy_list = ["2021-22", "2022-23", "2023-24", "2024-25"]
        assert EconomicDataContract.assert_no_mixed_periods(fy_list) == ReportingPeriodType.FINANCIAL_YEAR

    def test_assert_no_mixed_periods_rejection(self):
        """Raises ValueError when Calendar Year and Financial Year observations are mixed."""
        mixed_list = ["2023-24", "2023", "2024"]
        with pytest.raises(ValueError, match="Mixed reporting period types detected"):
            EconomicDataContract.assert_no_mixed_periods(mixed_list)

    def test_currency_conversion(self):
        """Verifies mathematical exactness of USD and INR Crore unit conversions."""
        # 1 USD Billion = 1000 USD Million
        val_m = EconomicDataContract.to_usd_million(5.5, CurrencyUnit.USD_BILLION)
        assert val_m == 5500.0

        # 5500 USD Million = 5.5 USD Billion
        val_b = EconomicDataContract.to_usd_billion(5500.0, CurrencyUnit.USD_MILLION)
        assert val_b == 5.5

        # INR Crore conversion: 1 USD Billion at 83.50 INR/USD = 8,350 INR Crore
        # Formula: 10^9 USD * 83.5 / 10^7 = 8,350 Crore
        inr_cr = EconomicDataContract.to_inr_crore(1.0, exchange_rate=83.5)
        assert inr_cr == 8350.0

    def test_safe_share_valid(self):
        """Verifies safe percentage share computation."""
        share, meta = EconomicDataContract.safe_share(25.0, 100.0)
        assert share == 25.0
        assert meta["is_valid"] is True
        assert meta["data_limitation"] is None

    def test_safe_share_zero_or_negative_denominator(self):
        """Returns None with explicit data limitation flag when denominator is zero or negative."""
        share, meta = EconomicDataContract.safe_share(25.0, 0.0)
        assert share is None
        assert meta["is_valid"] is False
        assert "INVALID_DENOMINATOR" in meta["data_limitation"]

        share_neg, meta_neg = EconomicDataContract.safe_share(25.0, -10.0)
        assert share_neg is None
        assert meta_neg["is_valid"] is False


class TestTradeDependencyAnalyzer:
    """Verifies HHI, concentration ratios, coverage auditing, and trend analyses."""

    def test_hhi_textbook_benchmarks(self):
        """Tests HHI against established mathematical textbook cases (0 - 10,000 scale)."""
        # Monopoly (1 firm with 100%): 100^2 = 10,000
        res_monopoly = TradeDependencyAnalyzer.calculate_hhi_with_coverage([100.0])
        assert res_monopoly["hhi_observed"] == 10000.0
        assert res_monopoly["concentration_status"] == "HIGHLY_CONCENTRATED"

        # Equal Duopoly (2 firms with 50% each): 50^2 + 50^2 = 5,000
        res_duopoly = TradeDependencyAnalyzer.calculate_hhi_with_coverage([50.0, 50.0])
        assert res_duopoly["hhi_observed"] == 5000.0
        assert res_duopoly["concentration_status"] == "HIGHLY_CONCENTRATED"

        # Equal Quadropoly (4 firms with 25% each): 4 * 25^2 = 2,500
        res_quad = TradeDependencyAnalyzer.calculate_hhi_with_coverage([25.0, 25.0, 25.0, 25.0])
        assert res_quad["hhi_observed"] == 2500.0

        # Equal 10-firm market (10 firms with 10% each): 10 * 10^2 = 1,000
        res_ten = TradeDependencyAnalyzer.calculate_hhi_with_coverage([10.0] * 10)
        assert res_ten["hhi_observed"] == 1000.0
        assert res_ten["concentration_status"] == "DIVERSIFIED"

    def test_hhi_coverage_warning(self):
        """Emits explicit data limitation warning when partner coverage is below 85%."""
        # Only 60% coverage
        res_partial = TradeDependencyAnalyzer.calculate_hhi_with_coverage([30.0, 20.0, 10.0])
        assert res_partial["coverage_pct"] == 60.0
        assert res_partial["unobserved_pct"] == 40.0
        assert res_partial["coverage_warning"] is not None
        assert "DATA LIMITATION WARNING" in res_partial["coverage_warning"]
        # Max bound: observed + (40)^2 = (900 + 400 + 100) + 1600 = 1400 + 1600 = 3000
        assert res_partial["hhi_observed"] == 1400.0
        assert res_partial["hhi_max_bound"] == 3000.0

    @pytest.fixture
    def sample_cpt_df(self):
        """Creates an empirical-style commodity partner DataFrame."""
        return pd.DataFrame([
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Russia", "partner_iso3": "RUS", "value_usd_million": 45000.0, "value_usd_billion": 45.0, "partner_share_pct": 36.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Iraq", "partner_iso3": "IRQ", "value_usd_million": 25000.0, "value_usd_billion": 25.0, "partner_share_pct": 20.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Saudi Arabia", "partner_iso3": "SAU", "value_usd_million": 20000.0, "value_usd_billion": 20.0, "partner_share_pct": 16.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "UAE", "partner_iso3": "ARE", "value_usd_million": 12500.0, "value_usd_billion": 12.5, "partner_share_pct": 10.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "USA", "partner_iso3": "USA", "value_usd_million": 10000.0, "value_usd_billion": 10.0, "partner_share_pct": 8.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Kuwait", "partner_iso3": "KWT", "value_usd_million": 6250.0, "value_usd_billion": 6.25, "partner_share_pct": 5.0},
            {"financial_year": "2023-24", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Nigeria", "partner_iso3": "NGA", "value_usd_million": 6250.0, "value_usd_billion": 6.25, "partner_share_pct": 5.0},
            # Previous year for trend
            {"financial_year": "2022-23", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Russia", "partner_iso3": "RUS", "value_usd_million": 30000.0, "value_usd_billion": 30.0, "partner_share_pct": 22.0},
            {"financial_year": "2022-23", "commodity_group": "Crude Petroleum", "trade_flow": "Import",
             "partner_country": "Iraq", "partner_iso3": "IRQ", "value_usd_million": 30000.0, "value_usd_billion": 30.0, "partner_share_pct": 22.0},
        ])

    def test_analyze_dependency_metrics(self, sample_cpt_df):
        """Verifies full cross-sectional dependency analysis on sample trade records."""
        analysis = TradeDependencyAnalyzer.analyze_dependency(
            df_commodity_partner=sample_cpt_df,
            commodity_group="Crude Petroleum",
            trade_flow="Import",
            financial_year="2023-24"
        )

        assert analysis["commodity_group"] == "Crude Petroleum"
        assert analysis["top_1_partner"] == "Russia"
        assert analysis["top_1_share_pct"] == 36.0
        assert analysis["top_1_value_usd_billion"] == 45.0

        # CR5 = 36 + 20 + 16 + 10 + 8 = 90.0%
        assert analysis["top_5_share_pct"] == 90.0

        # Coverage = 36 + 20 + 16 + 10 + 8 + 5 + 5 = 100.0%
        assert analysis["coverage_pct"] == 100.0
        assert analysis["coverage_warning"] is None

        # HHI = 36^2 + 20^2 + 16^2 + 10^2 + 8^2 + 5^2 + 5^2
        # = 1296 + 400 + 256 + 100 + 64 + 25 + 25 = 2166.0
        assert analysis["hhi_score"] == 2166.0
        assert analysis["concentration_status"] == "MODERATE"

        # Check provenance attached
        assert "_provenance" in analysis
        assert "Directorate General" in analysis["_provenance"]["source"]

    def test_historical_dependency_trends(self, sample_cpt_df):
        """Verifies multi-year trend extraction filters correctly."""
        df_trends = TradeDependencyAnalyzer.get_historical_dependency_trends(
            sample_cpt_df, commodity_group="Crude Petroleum", trade_flow="Import", top_n_partners=2
        )
        assert not df_trends.empty
        assert set(df_trends["partner_country"].unique()) == {"Russia", "Iraq"}
        assert len(df_trends["financial_year"].unique()) == 2
