"""Tests for statistical modeling, OLS trend, structural break estimation, and inflation purchasing power."""
import pandas as pd
from india_trade_intelligence.src.analysis.econometrics import EconometricAnalyzer

def test_ols_trend_perfect_line():
    # y = 10 * x + 50
    s = pd.Series([50.0, 60.0, 70.0, 80.0, 90.0])
    res = EconometricAnalyzer.calculate_ols_trend(s)
    assert res["slope"] == 10.0
    assert res["intercept"] == 50.0
    assert res["r_squared"] == 1.0

def test_structural_breaks():
    # Mock data spanning 2015 to 2024
    years = list(range(2015, 2025))
    df = pd.DataFrame({
        "year": years,
        "exports_usd_billion": [400.0 if y <= 2019 else (450.0 if y == 2020 else 700.0) for y in years],
        "imports_usd_billion": [500.0 if y <= 2019 else (520.0 if y == 2020 else 850.0) for y in years],
        "trade_balance_usd_billion": [-100.0 if y <= 2019 else (-70.0 if y == 2020 else -150.0) for y in years],
        "calculated_trade_openness_pct": [35.0 if y <= 2019 else 42.0 for y in years]
    })

    sb = EconometricAnalyzer.analyze_structural_breaks(df)
    assert sb["pre_covid_avg_exports_usd_b"] == 400.0
    assert sb["post_covid_avg_exports_usd_b"] == 700.0
    assert sb["exports_expansion_pct"] == 75.0

def test_causality_disclaimer_present():
    disclaimer = EconometricAnalyzer.get_causality_disclaimer()
    assert "Correlation does NOT imply causation" in disclaimer
    assert "general-equilibrium" in disclaimer

def test_cpi_and_purchasing_power_decay():
    # Mock annual inflation rates
    df_macro = pd.DataFrame({
        "year": [2000, 2001, 2002],
        "cpi_inflation_pct": [5.0, 10.0, 10.0]
    })
    pp_df = EconometricAnalyzer.calculate_purchasing_power_decay(df_macro, start_year=2000, initial_amount=1000.0)
    assert not pp_df.empty
    # Base year purchasing power equals initial amount
    assert pp_df.loc[pp_df["year"] == 2000, "real_purchasing_power_inr"].iloc[0] == 1000.0
    # Next year purchasing power decreases as prices rise
    assert pp_df.loc[pp_df["year"] == 2001, "real_purchasing_power_inr"].iloc[0] < 1000.0

def test_commodity_basket_affordability():
    basket_2000 = EconometricAnalyzer.get_representative_commodity_basket(2000, 1000.0)
    basket_2024 = EconometricAnalyzer.get_representative_commodity_basket(2024, 1000.0)
    
    # 1000 Rs bought more rice and petrol in 2000 than in 2024
    assert basket_2000["Rice (Staple Food)"]["quantity_affordable"] > basket_2024["Rice (Staple Food)"]["quantity_affordable"]
    assert basket_2000["Petrol (Transport Energy)"]["quantity_affordable"] > basket_2024["Petrol (Transport Energy)"]["quantity_affordable"]

def test_inflation_halving_time():
    # At 7% inflation, halving time is 10 years (70 / 7)
    halving = EconometricAnalyzer.get_inflation_halving_time(7.0)
    assert halving == 10.0
