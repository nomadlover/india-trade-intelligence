"""Econometric analysis and statistical modeling module for India's trade dynamics.
Implements OLS secular trends, structural break comparisons, partner/commodity concentration,
inflation purchasing power decay, real vs nominal trade deflators, and statistical guardrails.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List

class EconometricAnalyzer:
    """Executes research-grade statistical and econometric evaluations."""

    @staticmethod
    def calculate_ols_trend(series: pd.Series) -> Dict[str, Any]:
        """Performs Ordinary Least Squares (OLS) linear trend regression over a time series.
        
        Returns:
            Dictionary with annual slope, intercept, R-squared, and annualized growth trend.
        """
        clean = series.dropna()
        n = len(clean)
        if n < 3:
            return {"slope": 0.0, "intercept": 0.0, "r_squared": 0.0, "p_value_approx": 1.0}

        x = np.arange(n)
        y = clean.values

        # Linear regression formulas
        x_mean, y_mean = np.mean(x), np.mean(y)
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return {"slope": 0.0, "intercept": y_mean, "r_squared": 0.0, "p_value_approx": 1.0}

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Annualized average growth rate across trend
        trend_cagr = (slope / y_mean) * 100.0 if y_mean != 0 else 0.0

        return {
            "slope": round(float(slope), 3),
            "intercept": round(float(intercept), 3),
            "r_squared": round(float(r_squared), 4),
            "average_annual_increment": round(float(slope), 2),
            "annualized_trend_pct": round(float(trend_cagr), 2)
        }

    @staticmethod
    def analyze_structural_breaks(df_macro: pd.DataFrame) -> Dict[str, Any]:
        """Evaluates structural shifts across major economic eras:
        1. Pre-COVID Era (2015-2019)
        2. Pandemic Disruption (2020)
        3. Post-Pandemic Rebound & Global Re-alignment (2021-2024)
        """
        df = df_macro.copy()
        pre_covid = df[(df["year"] >= 2015) & (df["year"] <= 2019)]
        post_covid = df[(df["year"] >= 2021) & (df["year"] <= 2024)]

        pre_exp_mean = pre_covid["exports_usd_billion"].mean() if not pre_covid.empty else 0
        post_exp_mean = post_covid["exports_usd_billion"].mean() if not post_covid.empty else 0

        pre_imp_mean = pre_covid["imports_usd_billion"].mean() if not pre_covid.empty else 0
        post_imp_mean = post_covid["imports_usd_billion"].mean() if not post_covid.empty else 0

        pre_def_mean = pre_covid["trade_balance_usd_billion"].mean() if not pre_covid.empty else 0
        post_def_mean = post_covid["trade_balance_usd_billion"].mean() if not post_covid.empty else 0

        pre_openness = pre_covid["calculated_trade_openness_pct"].mean() if "calculated_trade_openness_pct" in pre_covid.columns else 0
        post_openness = post_covid["calculated_trade_openness_pct"].mean() if "calculated_trade_openness_pct" in post_covid.columns else 0

        exp_surge_pct = ((post_exp_mean - pre_exp_mean) / pre_exp_mean * 100) if pre_exp_mean > 0 else 0
        imp_surge_pct = ((post_imp_mean - pre_imp_mean) / pre_imp_mean * 100) if pre_imp_mean > 0 else 0

        return {
            "pre_covid_period": "2015-2019",
            "post_covid_period": "2021-2024",
            "pre_covid_avg_exports_usd_b": round(float(pre_exp_mean), 2),
            "post_covid_avg_exports_usd_b": round(float(post_exp_mean), 2),
            "exports_expansion_pct": round(float(exp_surge_pct), 2),
            "pre_covid_avg_imports_usd_b": round(float(pre_imp_mean), 2),
            "post_covid_avg_imports_usd_b": round(float(post_imp_mean), 2),
            "imports_expansion_pct": round(float(imp_surge_pct), 2),
            "pre_covid_avg_deficit_usd_b": round(float(pre_def_mean), 2),
            "post_covid_avg_deficit_usd_b": round(float(post_def_mean), 2),
            "pre_covid_avg_openness_pct": round(float(pre_openness), 2),
            "post_covid_avg_openness_pct": round(float(post_openness), 2)
        }

    @staticmethod
    def calculate_correlation_matrix(df: pd.DataFrame, variables: list) -> pd.DataFrame:
        """Computes Pearson correlation coefficients with pairwise completeness."""
        valid_cols = [c for c in variables if c in df.columns]
        if len(valid_cols) < 2:
            return pd.DataFrame()
        return df[valid_cols].corr().round(3)

    @staticmethod
    def calculate_cpi_index(df_macro: pd.DataFrame, base_year: int = 2000) -> pd.DataFrame:
        """Calculates cumulative Consumer Price Index (CPI Base Year = 100) from annual CPI inflation rates."""
        df = df_macro[["year", "cpi_inflation_pct"]].dropna().sort_values("year").copy()
        if df.empty:
            return pd.DataFrame()

        # Cumulative CPI index compounding from base year
        # First set base year index to 100.0
        cpi_dict = {base_year: 100.0}
        
        # Forward calculation from base_year
        future_years = [y for y in df["year"].unique() if y > base_year]
        for y in sorted(future_years):
            inf_val = df.loc[df["year"] == y, "cpi_inflation_pct"].iloc[0]
            prev_cpi = cpi_dict[y - 1] if (y - 1) in cpi_dict else 100.0
            cpi_dict[y] = prev_cpi * (1.0 + (inf_val / 100.0))

        # Backward calculation for years prior to base_year
        past_years = [y for y in df["year"].unique() if y < base_year]
        for y in sorted(past_years, reverse=True):
            inf_val = df.loc[df["year"] == y + 1, "cpi_inflation_pct"].iloc[0]
            next_cpi = cpi_dict[y + 1] if (y + 1) in cpi_dict else 100.0
            cpi_dict[y] = next_cpi / (1.0 + (inf_val / 100.0))

        df["cpi_index_base2000"] = df["year"].map(cpi_dict).round(2)
        return df

    @classmethod
    def calculate_purchasing_power_decay(cls, df_macro: pd.DataFrame, start_year: int, initial_amount: float = 1000.0) -> pd.DataFrame:
        """Calculates the real purchasing power trajectory of a fixed nominal rupee amount across time."""
        cpi_df = cls.calculate_cpi_index(df_macro, base_year=start_year)
        if cpi_df.empty or start_year not in cpi_df["year"].values:
            return pd.DataFrame()

        # In start_year, price index = 100.0, purchasing power = initial_amount
        start_cpi = cpi_df.loc[cpi_df["year"] == start_year, "cpi_index_base2000"].iloc[0]
        
        # Purchasing power at year t = initial_amount * (start_cpi / current_cpi)
        cpi_df["real_purchasing_power_inr"] = (initial_amount * (start_cpi / cpi_df["cpi_index_base2000"])).round(2)
        cpi_df["purchasing_power_retention_pct"] = ((cpi_df["real_purchasing_power_inr"] / initial_amount) * 100.0).round(2)
        cpi_df["cumulative_inflation_pct"] = (((cpi_df["cpi_index_base2000"] / start_cpi) - 1.0) * 100.0).round(2)
        
        return cpi_df

    @staticmethod
    def get_representative_commodity_basket(year: int, amount: float) -> Dict[str, Dict[str, Any]]:
        """Calculates physical purchasing volume for essential Indian consumer and economic goods.
        
        Benchmark representative prices across Indian economic history (1995 to 2025).
        """
        # Price table (year: {item: price_in_inr})
        price_benchmarks = {
            1995: {"rice_kg": 9.5, "petrol_l": 18.0, "lpg_cylinder": 135.0, "cinema_ticket": 15.0, "gold_gram": 468.0, "thali_meal": 10.0},
            2000: {"rice_kg": 13.5, "petrol_l": 28.5, "lpg_cylinder": 210.0, "cinema_ticket": 35.0, "gold_gram": 440.0, "thali_meal": 18.0},
            2005: {"rice_kg": 17.0, "petrol_l": 43.5, "lpg_cylinder": 295.0, "cinema_ticket": 70.0, "gold_gram": 700.0, "thali_meal": 28.0},
            2010: {"rice_kg": 26.0, "petrol_l": 55.0, "lpg_cylinder": 345.0, "cinema_ticket": 120.0, "gold_gram": 1850.0, "thali_meal": 45.0},
            2015: {"rice_kg": 38.0, "petrol_l": 66.0, "lpg_cylinder": 610.0, "cinema_ticket": 180.0, "gold_gram": 2630.0, "thali_meal": 65.0},
            2020: {"rice_kg": 48.0, "petrol_l": 81.0, "lpg_cylinder": 690.0, "cinema_ticket": 250.0, "gold_gram": 4860.0, "thali_meal": 95.0},
            2024: {"rice_kg": 60.0, "petrol_l": 97.0, "lpg_cylinder": 850.0, "cinema_ticket": 320.0, "gold_gram": 7200.0, "thali_meal": 125.0},
            2025: {"rice_kg": 64.0, "petrol_l": 98.0, "lpg_cylinder": 870.0, "cinema_ticket": 350.0, "gold_gram": 7800.0, "thali_meal": 135.0}
        }

        # Select nearest benchmark year
        available_years = sorted(price_benchmarks.keys())
        nearest_year = min(available_years, key=lambda y: abs(y - year))
        prices = price_benchmarks[nearest_year]

        basket = {
            "Rice (Staple Food)": {
                "unit": "kg",
                "unit_price_inr": prices["rice_kg"],
                "quantity_affordable": round(amount / prices["rice_kg"], 1),
                "icon": "🌾"
            },
            "Petrol (Transport Energy)": {
                "unit": "litres",
                "unit_price_inr": prices["petrol_l"],
                "quantity_affordable": round(amount / prices["petrol_l"], 1),
                "icon": "⛽"
            },
            "LPG Domestic Cooking Gas": {
                "unit": "cylinders (14.2kg)",
                "unit_price_inr": prices["lpg_cylinder"],
                "quantity_affordable": round(amount / prices["lpg_cylinder"], 2),
                "icon": "🔥"
            },
            "Wholesome Meal / Thali": {
                "unit": "meals",
                "unit_price_inr": prices["thali_meal"],
                "quantity_affordable": round(amount / prices["thali_meal"], 1),
                "icon": "🍲"
            },
            "Cinema Entertainment Ticket": {
                "unit": "tickets",
                "unit_price_inr": prices["cinema_ticket"],
                "quantity_affordable": round(amount / prices["cinema_ticket"], 1),
                "icon": "🎟️"
            },
            "24K Physical Gold": {
                "unit": "grams",
                "unit_price_inr": prices["gold_gram"],
                "quantity_affordable": round(amount / prices["gold_gram"], 3),
                "icon": "🪙"
            }
        }
        return basket

    @staticmethod
    def get_inflation_halving_time(mean_inflation_pct: float) -> float:
        """Calculates Rule of 70 doubling/halving time for purchasing power."""
        if mean_inflation_pct <= 0:
            return float("inf")
        return round(70.0 / mean_inflation_pct, 1)

    @staticmethod
    def get_causality_disclaimer() -> str:
        """Returns standard econometric guidance on correlation vs causation."""
        return (
            "METHODOLOGICAL GUARDRAIL: Correlation does NOT imply causation. "
            "Observed statistical co-movements (e.g. between the INR/USD exchange rate "
            "and export earnings, or domestic GDP growth and import demand) reflect "
            "complex general-equilibrium interactions influenced by global commodity price cycles, "
            "multilateral tariff structures, terms-of-trade shocks, and domestic monetary policies. "
            "Direct causal claims require exogenous instruments, structural vector autoregressions (SVAR), "
            "or rigorous natural experiment identification strategies."
        )
