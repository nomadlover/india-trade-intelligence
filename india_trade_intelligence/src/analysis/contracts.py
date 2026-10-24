"""Shared Economic Data Contract and Validation Utility.
Enforces:
1. Target period type verification (CY vs FY vs Monthly) preventing period mixing.
2. Currency/unit standardization and conversion helpers (USD Million, USD Billion, INR Crore).
3. Safe division and share computation with zero/negative denominator guardrails.
4. Transparent data limitation flags and research disclaimers.
5. Research-grade provenance tracking attached to analysis outputs.
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Iterable, Union
import math
import pandas as pd
import numpy as np


class ReportingPeriodType(str, Enum):
    """Classification of time series reporting periods."""
    FINANCIAL_YEAR = "FINANCIAL_YEAR"  # Indian Fiscal Year: April 1 to March 31 (e.g., '2023-24' or 'FY24')
    CALENDAR_YEAR = "CALENDAR_YEAR"    # January 1 to December 31 (e.g., 2023 or '2023')
    MONTHLY = "MONTHLY"                # Monthly frequency (e.g., '2024-04' or 'Apr-2024')
    UNKNOWN = "UNKNOWN"


class CurrencyUnit(str, Enum):
    """Standardized currency and scale denominations."""
    USD_MILLION = "USD_MILLION"
    USD_BILLION = "USD_BILLION"
    INR_CRORE = "INR_CRORE"


class EconomicDataContract:
    """Core contract enforcing mathematical and reporting integrity across analytical services."""

    @staticmethod
    def detect_period_type(period: Union[str, int]) -> ReportingPeriodType:
        """Determines the reporting period type from string or integer representation."""
        if period is None:
            return ReportingPeriodType.UNKNOWN
            
        p_str = str(period).strip()
        
        # FY format: e.g., '2023-24', '2023-2024', 'FY24', 'FY2024'
        if "-" in p_str:
            parts = p_str.split("-")
            if len(parts) == 2:
                # Could be 2023-24 (FY) or 2023-04 (Monthly)
                if len(parts[0]) == 4 and parts[0].isdigit():
                    if len(parts[1]) in (2, 4) and parts[1].isdigit():
                        p1_val = int(parts[1])
                        # If second part is 01-12 and formatted with 2 digits, could be monthly unless fiscal year context
                        # Standard DGCI&S fiscal year format is 2023-24 (where 24 is next year)
                        # If year is 2023 and next is 24, it's definitely FY
                        y0 = int(parts[0])
                        if len(parts[1]) == 2 and (p1_val == (y0 + 1) % 100 or p1_val == y0 % 100):
                            return ReportingPeriodType.FINANCIAL_YEAR
                        elif len(parts[1]) == 4 and p1_val == y0 + 1:
                            return ReportingPeriodType.FINANCIAL_YEAR
                        elif 1 <= p1_val <= 12 and len(parts[1]) == 2:
                            return ReportingPeriodType.MONTHLY
                        return ReportingPeriodType.FINANCIAL_YEAR
        
        if p_str.upper().startswith("FY"):
            return ReportingPeriodType.FINANCIAL_YEAR
            
        # 4-digit calendar year
        if p_str.isdigit() and len(p_str) == 4:
            return ReportingPeriodType.CALENDAR_YEAR
            
        # Check for month-year pattern e.g. 'Apr-2024'
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        if any(m in p_str.upper() for m in months):
            return ReportingPeriodType.MONTHLY
            
        return ReportingPeriodType.UNKNOWN

    @classmethod
    def assert_no_mixed_periods(cls, periods: Iterable[Union[str, int]]) -> ReportingPeriodType:
        """Validates that a collection of periods does not mix CY and FY.
        Raises ValueError if inconsistent period types are mixed.
        """
        detected_types = set()
        for p in periods:
            if pd.isna(p):
                continue
            pt = cls.detect_period_type(p)
            if pt != ReportingPeriodType.UNKNOWN:
                detected_types.add(pt)
                
        if len(detected_types) > 1:
            types_str = ", ".join(t.value for t in detected_types)
            raise ValueError(
                f"ECONOMIC DATA CONTRACT VIOLATION: Mixed reporting period types detected ({types_str}). "
                "Financial Year (FY April-March) and Calendar Year (CY Jan-Dec) observations must never be aggregated."
            )
            
        return next(iter(detected_types)) if detected_types else ReportingPeriodType.UNKNOWN

    @staticmethod
    def to_usd_billion(value: float, from_unit: CurrencyUnit, exchange_rate: float = 83.5) -> float:
        """Converts a nominal monetary figure to USD Billion."""
        if value is None or pd.isna(value):
            return float("nan")
            
        if from_unit == CurrencyUnit.USD_BILLION:
            return float(value)
        elif from_unit == CurrencyUnit.USD_MILLION:
            return float(value) / 1000.0
        elif from_unit == CurrencyUnit.INR_CRORE:
            # 1 USD Billion = 10^9 USD = (10^9 * exchange_rate) INR
            # 1 Crore = 10^7 INR => 1 USD Billion = 100 * exchange_rate INR Crore
            # Therefore USD Billion = INR Crore / (100 * exchange_rate)
            if exchange_rate <= 0:
                raise ValueError(f"Exchange rate must be positive, got {exchange_rate}")
            return float(value) / (100.0 * exchange_rate)
        else:
            raise ValueError(f"Unsupported CurrencyUnit: {from_unit}")

    @staticmethod
    def to_usd_million(value: float, from_unit: CurrencyUnit, exchange_rate: float = 83.5) -> float:
        """Converts a nominal monetary figure to USD Million."""
        usd_b = EconomicDataContract.to_usd_billion(value, from_unit, exchange_rate)
        return usd_b * 1000.0 if not pd.isna(usd_b) else float("nan")

    @staticmethod
    def to_inr_crore(value_usd_billion: float, exchange_rate: float = 83.5) -> float:
        """Converts USD Billion to INR Crore at specified exchange rate.
        Formula: 1 USD Billion = 100 * exchange_rate (INR Crore).
        """
        if value_usd_billion is None or pd.isna(value_usd_billion):
            return float("nan")
        if exchange_rate <= 0:
            raise ValueError(f"Exchange rate must be positive, got {exchange_rate}")
        return float(value_usd_billion) * exchange_rate * 100.0

    @staticmethod
    def safe_share(
        part: float,
        total: float,
        min_denominator: float = 1e-6
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Calculates percentage share (0-100%) safely without silent division by zero.
        Returns:
            Tuple of (share_pct, metadata_dict)
            If denominator is invalid, share_pct is None and metadata records limitation.
        """
        meta: Dict[str, Any] = {
            "is_valid": True,
            "data_limitation": None
        }
        
        if pd.isna(part) or pd.isna(total):
            meta["is_valid"] = False
            meta["data_limitation"] = "MISSING_VALUE: One or both inputs are NaN/None."
            return None, meta
            
        if total <= min_denominator:
            meta["is_valid"] = False
            meta["data_limitation"] = f"INVALID_DENOMINATOR: Denominator {total} <= {min_denominator}."
            return None, meta
            
        if part < 0:
            meta["is_valid"] = False
            meta["data_limitation"] = f"NEGATIVE_NUMERATOR: Trade values cannot be negative, got {part}."
            return None, meta
            
        share = round((part / total) * 100.0, 4)
        return share, meta

    @staticmethod
    def attach_provenance(
        result: Dict[str, Any],
        source: str,
        target_period: str,
        methodology: str,
        coverage_pct: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Attaches standardized empirical provenance metadata to an analysis payload."""
        enriched = dict(result)
        enriched["_provenance"] = {
            "source": source,
            "target_period": target_period,
            "methodology": methodology,
            "coverage_pct": round(coverage_pct, 2) if coverage_pct is not None else None,
            "notes": notes or "Calculated directly from validated official trade data.",
            "disclaimer": "Scenario and risk computations are mechanical models for economic analysis, not official forecasts."
        }
        return enriched
