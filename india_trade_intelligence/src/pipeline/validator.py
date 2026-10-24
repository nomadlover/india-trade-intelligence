"""Rigorous data validation module for economic and international trade statistics.
Validates structural schemas, economic accounting identities, ranges, and temporal formats.
"""
import re
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from india_trade_intelligence.src.config import COUNTRY_ISO_MAP

@dataclass
class ValidationReport:
    """Stores the audit outcome of a validation run."""
    dataset_name: str
    is_valid: bool = True
    total_records: int = 0
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_value_summary: Dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Validation [{status}] for {self.dataset_name} "
            f"({self.total_records} rows). "
            f"Passed: {len(self.passed_checks)}, Failed: {len(self.failed_checks)}, "
            f"Warnings: {len(self.warnings)}"
        )


class TradeDataValidator:
    """Performs statistical and econometric validation on trade datasets."""

    @staticmethod
    def validate_world_bank_payload(payload: Dict[str, Any]) -> ValidationReport:
        """Validates the raw World Bank indicators JSON structure."""
        report = ValidationReport(dataset_name="World Bank Macro Indicators")
        if not isinstance(payload, dict) or "indicators" not in payload:
            report.is_valid = False
            report.failed_checks.append("Payload missing root 'indicators' object.")
            return report

        indicators = payload["indicators"]
        report.passed_checks.append("Root payload format valid.")

        total_obs = 0
        for ind_key, ind_data in indicators.items():
            records = ind_data.get("records", [])
            total_obs += len(records)
            if not records:
                report.warnings.append(f"Indicator '{ind_key}' contains 0 records.")
                continue

            # Validate date formats and non-negativity where applicable
            for rec in records:
                date_val = rec.get("date")
                val = rec.get("value")
                if date_val and not str(date_val).isdigit():
                    report.failed_checks.append(f"Invalid date format '{date_val}' in {ind_key}")
                    report.is_valid = False
                if val is not None and ind_key in ["exports_gnfs", "imports_gnfs", "gdp_current_usd"]:
                    if float(val) < 0:
                        report.failed_checks.append(f"Negative value {val} found in {ind_key}")
                        report.is_valid = False

        report.total_records = total_obs
        if not report.failed_checks:
            report.passed_checks.append("All observation dates and non-negativity constraints valid.")
        return report

    @staticmethod
    def validate_bilateral_trade(df: pd.DataFrame) -> ValidationReport:
        """Validates bilateral partner trade data."""
        report = ValidationReport(dataset_name="DGCI&S Bilateral Trade", total_records=len(df))

        # 1. Required columns
        required_cols = [
            "financial_year", "country", "exports_usd_million",
            "imports_usd_million", "trade_balance_usd_million", "total_trade_usd_million"
        ]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing_cols}")
            return report
        report.passed_checks.append("Schema check passed: all required columns present.")

        # 2. Missing data check
        null_counts = df[required_cols].isnull().sum().to_dict()
        report.missing_value_summary = {k: v for k, v in null_counts.items() if v > 0}
        if any(v > 0 for v in null_counts.values()):
            report.warnings.append(f"Found missing values: {report.missing_value_summary}")

        # 3. Non-negativity checks
        if (df["exports_usd_million"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Negative exports found in bilateral trade.")
        else:
            report.passed_checks.append("Non-negativity constraint satisfied for exports.")

        if (df["imports_usd_million"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Negative imports found in bilateral trade.")
        else:
            report.passed_checks.append("Non-negativity constraint satisfied for imports.")

        # 4. Accounting identity: Trade Balance == Exports - Imports (tolerance $0.05M)
        diff_bal = (df["trade_balance_usd_million"] - (df["exports_usd_million"] - df["imports_usd_million"])).abs()
        if (diff_bal > 0.05).any():
            max_err = diff_bal.max()
            report.is_valid = False
            report.failed_checks.append(f"Accounting identity violation (Balance != Exp - Imp). Max error: {max_err}")
        else:
            report.passed_checks.append("Accounting identity verified: Trade Balance == Exports - Imports.")

        # 5. Accounting identity: Total Trade == Exports + Imports
        diff_tot = (df["total_trade_usd_million"] - (df["exports_usd_million"] + df["imports_usd_million"])).abs()
        if (diff_tot > 0.05).any():
            max_err = diff_tot.max()
            report.is_valid = False
            report.failed_checks.append(f"Accounting identity violation (Total != Exp + Imp). Max error: {max_err}")
        else:
            report.passed_checks.append("Accounting identity verified: Total Trade == Exports + Imports.")

        # 6. Financial Year regex format check (e.g., 2023-24)
        fy_pattern = re.compile(r"^\d{4}-\d{2}$")
        invalid_fy = df[~df["financial_year"].astype(str).str.match(fy_pattern)]
        if not invalid_fy.empty:
            report.is_valid = False
            report.failed_checks.append(f"Found {len(invalid_fy)} records with invalid FY format.")
        else:
            report.passed_checks.append("Financial year formatting valid (YYYY-YY).")

        # 7. Country coverage and mapping
        unmapped_countries = [c for c in df["country"].unique() if c not in COUNTRY_ISO_MAP]
        if unmapped_countries:
            report.warnings.append(f"Countries lacking ISO-3 standard mapping: {unmapped_countries}")
        else:
            report.passed_checks.append("All country entities correctly mapped to ISO-3 identifiers.")

        return report

    @staticmethod
    def validate_commodity_trade(df: pd.DataFrame) -> ValidationReport:
        """Validates principal commodity group trade dataset."""
        report = ValidationReport(dataset_name="DGCI&S Commodity Trade", total_records=len(df))

        required_cols = ["financial_year", "commodity_group", "trade_flow", "value_usd_million"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing_cols}")
            return report
        report.passed_checks.append("Schema check passed.")

        # Non-negativity
        if (df["value_usd_million"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Negative commodity values detected.")
        else:
            report.passed_checks.append("Non-negativity verified for commodity trade values.")

        # Valid trade flow categories
        valid_flows = {"Export", "Import"}
        actual_flows = set(df["trade_flow"].unique())
        invalid_flows = actual_flows - valid_flows
        if invalid_flows:
            report.is_valid = False
            report.failed_checks.append(f"Invalid trade flow values: {invalid_flows}")
        else:
            report.passed_checks.append("Trade flow values valid ('Export' / 'Import').")

        # Financial year format
        fy_pattern = re.compile(r"^\d{4}-\d{2}$")
        if not df["financial_year"].astype(str).str.match(fy_pattern).all():
            report.is_valid = False
            report.failed_checks.append("Invalid FY format in commodity dataset.")
        else:
            report.passed_checks.append("Financial year formatting verified.")

        return report

    @staticmethod
    def validate_monthly_trade(df: pd.DataFrame) -> ValidationReport:
        """Validates monthly high-frequency merchandise trade dataset."""
        report = ValidationReport(dataset_name="RBI Monthly Trade", total_records=len(df))

        required_cols = [
            "period", "year", "month",
            "merchandise_exports_usd_million",
            "merchandise_imports_usd_million",
            "merchandise_trade_balance_usd_million"
        ]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing_cols}")
            return report
        report.passed_checks.append("Schema check passed.")

        # Date format YYYY-MM
        period_pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
        if not df["period"].astype(str).str.match(period_pattern).all():
            report.is_valid = False
            report.failed_checks.append("Invalid period format (expected YYYY-MM).")
        else:
            report.passed_checks.append("Period formatting verified (YYYY-MM).")

        # Accounting balance identity
        diff = (df["merchandise_trade_balance_usd_million"] - (
            df["merchandise_exports_usd_million"] - df["merchandise_imports_usd_million"]
        )).abs()
        if (diff > 0.05).any():
            report.is_valid = False
            report.failed_checks.append("Monthly merchandise trade balance identity violation.")
        else:
            report.passed_checks.append("Monthly merchandise balance identity confirmed.")

        return report

    @staticmethod
    def validate_commodity_price_quantity(df: pd.DataFrame) -> ValidationReport:
        """Validates commodity price-quantity and unit-value decomposition dataset."""
        report = ValidationReport(dataset_name="Commodity Price-Quantity Decomposition", total_records=len(df))
        required = ["financial_year", "commodity_group", "trade_flow", "value_usd_million", "quantity", "unit_value_usd_per_unit"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")

        # Non-negativity check
        if (df["value_usd_million"] < 0).any() or (df["quantity"] < 0).any() or (df["unit_value_usd_per_unit"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Negative value, quantity, or unit value detected.")
        else:
            report.passed_checks.append("Non-negativity verified for price-quantity series.")

        return report

    @staticmethod
    def validate_energy_commodity_exposure(df: pd.DataFrame) -> ValidationReport:
        """Validates energy and strategic commodity exposure metrics."""
        report = ValidationReport(dataset_name="Energy & Commodity Exposure", total_records=len(df))
        required = ["year", "brent_crude_usd_per_bbl", "indian_basket_crude_usd_per_bbl", "crude_import_bill_usd_billion"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")

        # Crude prices non-negativity
        if (df["brent_crude_usd_per_bbl"] <= 0).any() or (df["indian_basket_crude_usd_per_bbl"] <= 0).any():
            report.is_valid = False
            report.failed_checks.append("Non-positive benchmark crude price found.")
        else:
            report.passed_checks.append("Benchmark crude prices positive.")

        return report

    @staticmethod
    def validate_external_sector_macro(df: pd.DataFrame) -> ValidationReport:
        """Validates external sector and domestic macroeconomic series."""
        report = ValidationReport(dataset_name="External Sector & Macro Indicators", total_records=len(df))
        required = ["year", "inr_per_usd_exchange_rate", "fx_reserves_usd_billion", "real_gdp_growth_pct"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")

        if (df["inr_per_usd_exchange_rate"] <= 0).any() or (df["fx_reserves_usd_billion"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Invalid exchange rate or FX reserve values detected.")
        else:
            report.passed_checks.append("Exchange rates and FX reserves valid.")

        return report

    @staticmethod
    def validate_trading_partner_conditions(df: pd.DataFrame) -> ValidationReport:
        """Validates trading partner macroeconomic conditions."""
        report = ValidationReport(dataset_name="Trading Partner Conditions", total_records=len(df))
        required = ["year", "partner_name", "real_gdp_growth_pct", "cpi_inflation_pct"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")
        return report

    @staticmethod
    def validate_trade_policy_events(df: pd.DataFrame) -> ValidationReport:
        """Validates trade policy and geopolitical events catalog."""
        report = ValidationReport(dataset_name="Trade Policy Events", total_records=len(df))
        required = ["event_id", "effective_date", "title", "category", "verification_status"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")
        return report

    @staticmethod
    def validate_commodity_partner_trade(df: pd.DataFrame) -> ValidationReport:
        """Validates commodity-by-partner bilateral trade data."""
        report = ValidationReport(dataset_name="Commodity Partner Trade", total_records=len(df))
        required = [
            "financial_year", "commodity_group", "trade_flow",
            "partner_country", "value_usd_million", "partner_share_pct"
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.is_valid = False
            report.failed_checks.append(f"Missing required columns: {missing}")
            return report
        report.passed_checks.append("Schema check passed.")

        # Non-negativity check
        if (df["value_usd_million"] < 0).any() or (df["partner_share_pct"] < 0).any():
            report.is_valid = False
            report.failed_checks.append("Negative values or shares detected in commodity partner trade.")
        else:
            report.passed_checks.append("Non-negativity verified.")

        # Trade flow check
        valid_flows = {"Export", "Import"}
        if not set(df["trade_flow"].unique()).issubset(valid_flows):
            report.is_valid = False
            report.failed_checks.append("Invalid trade_flow values detected.")
        else:
            report.passed_checks.append("Trade flow values verified.")

        return report
