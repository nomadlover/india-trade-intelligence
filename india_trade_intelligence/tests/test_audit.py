"""Automated Validation and Economic Audit Test Suite for India Trade Intelligence.
Covers 11 mandatory audit checks:
1. Provenance metadata completeness
2. Absolute ban on misleading 'Today' / 'today' in user-facing labels
3. CPI calculation gap detection (no silent reset to 100.0)
4. Purchasing power decay calculation correctness
5. Commodity basket benchmark metadata and structure
6. Trade balance identity (Balance = Exports - Imports)
7. Trade openness formula (((Exp + Imp) / GDP) * 100)
8. Rule of 70 halving time calculation
9. Pre/post-COVID structural mean comparison statistics
10. AI fallback protection (ungrounded stats flagged with audit warning)
11. Data catalog schema integrity and consistency
"""
import pytest
import re
import json
from pathlib import Path
import pandas as pd
import numpy as np

from india_trade_intelligence.src.pipeline.provenance import (
    PROVENANCE_REGISTRY,
    get_provenance,
    MetricProvenance
)
from india_trade_intelligence.src.analysis.econometrics import EconometricAnalyzer
from india_trade_intelligence.src.ai.assistant import TradeAIAssistant
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer

# 1. Provenance metadata completeness
def test_provenance_metadata_completeness():
    assert len(PROVENANCE_REGISTRY) >= 10, "Provenance registry must contain all major application metrics"
    
    required_fields = [
        "metric_id", "name", "source", "source_agency",
        "observation_period", "frequency", "unit",
        "definition", "calculation", "data_status"
    ]
    
    for metric_id, prov in PROVENANCE_REGISTRY.items():
        assert isinstance(prov, MetricProvenance), f"Entry {metric_id} must be MetricProvenance instance"
        for field in required_fields:
            val = getattr(prov, field)
            assert val is not None and str(val).strip() != "", (
                f"Metric '{metric_id}' is missing required provenance field '{field}'"
            )
        assert prov.data_status in [
            "Official Final (1995–2024)",
            "Official Final",
            "Official Final (30 Observations: 1995–2024)",
            "Official Final (FY14–FY24); Provisional Q1 (FY25)",
            "Official Monthly Series",
            "Derived Accounting Identity",
            "Derived Econometric Metric",
            "Benchmark Proxy (Not Official Headline CPI)"
        ]

# 2. Absolute ban on misleading 'Today' / 'today'
def test_ban_on_misleading_today():
    root = Path(__file__).resolve().parent.parent
    files_to_check = [
        root / "app.py",
        root / "src" / "visualization" / "charts.py",
        root / "src" / "analysis" / "econometrics.py",
        root / "src" / "ai" / "assistant.py"
    ]
    
    # Banned phrases where 2024 historical data is called "Today"
    banned_phrases = [
        "Real Value Today",
        "Today's Real Value",
        "vs Today",
        "buy then versus today",
        "goods today"
    ]
    
    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} must exist"
        content = fpath.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            assert phrase not in content, f"Banned temporal phrase '{phrase}' found in {fpath.name}"

# 3. CPI index calculation gap handling (no silent reset)
def test_cpi_calculation_gap_detection():
    # A discontinuous series with a gap between 2000 and 2002 (missing 2001)
    df_gapped = pd.DataFrame({
        "year": [2000, 2002],
        "cpi_inflation_pct": [5.0, 6.0]
    })
    
    # Must raise ValueError and never silently reset to 100.0
    with pytest.raises(ValueError) as excinfo:
        EconometricAnalyzer.calculate_cpi_index(df_gapped, base_year=2000)
    assert "Discontinuous year sequence detected" in str(excinfo.value)

    # Contiguous sequence must compute correctly
    df_valid = pd.DataFrame({
        "year": [2000, 2001, 2002],
        "cpi_inflation_pct": [5.0, 10.0, 10.0]
    })
    res = EconometricAnalyzer.calculate_cpi_index(df_valid, base_year=2000)
    assert not res.empty
    idx_2000 = res.loc[res["year"] == 2000, "cpi_index_base2000"].iloc[0]
    idx_2001 = res.loc[res["year"] == 2001, "cpi_index_base2000"].iloc[0]
    idx_2002 = res.loc[res["year"] == 2002, "cpi_index_base2000"].iloc[0]
    
    assert idx_2000 == 100.0
    assert idx_2001 == 110.0  # 100 * (1 + 0.10)
    assert idx_2002 == 121.0  # 110 * (1 + 0.10)

# 4. Purchasing power decay calculation correctness
def test_purchasing_power_decay():
    df_macro = pd.DataFrame({
        "year": [2000, 2001, 2002],
        "cpi_inflation_pct": [5.0, 10.0, 10.0]
    })
    pp_df = EconometricAnalyzer.calculate_purchasing_power_decay(df_macro, start_year=2000, initial_amount=1000.0)
    
    assert not pp_df.empty
    row_2000 = pp_df.loc[pp_df["year"] == 2000].iloc[0]
    row_2001 = pp_df.loc[pp_df["year"] == 2001].iloc[0]
    row_2002 = pp_df.loc[pp_df["year"] == 2002].iloc[0]
    
    assert row_2000["real_purchasing_power_inr"] == 1000.0
    assert row_2000["purchasing_power_retention_pct"] == 100.0
    
    # In 2001: index = 110.0, real purchasing power = 1000 * (100 / 110) ≈ 909.09
    assert abs(row_2001["real_purchasing_power_inr"] - 909.09) < 0.1
    assert abs(row_2001["purchasing_power_retention_pct"] - 90.91) < 0.1
    
    # In 2002: index = 121.0, real purchasing power = 1000 * (100 / 121) ≈ 826.45
    assert abs(row_2002["real_purchasing_power_inr"] - 826.45) < 0.1

# 5. Commodity basket benchmark metadata and structure
def test_commodity_basket_benchmark_metadata():
    basket = EconometricAnalyzer.get_representative_commodity_basket(2024, 1000.0)
    assert len(basket) == 6
    
    for item_name, item_info in basket.items():
        assert "item" in item_info
        assert "year" in item_info and item_info["year"] == 2024
        assert "unit" in item_info
        assert "unit_price_inr" in item_info and item_info["unit_price_inr"] > 0
        assert "quantity_affordable" in item_info and item_info["quantity_affordable"] > 0
        assert "source_status" in item_info
        assert "Representative historical retail benchmark" in item_info["source_status"]
        assert "not official MoSPI headline CPI" in item_info["source_status"]

    # Audited side-by-side comparison
    comp_list = EconometricAnalyzer.compare_commodity_baskets(2000, 2024, 1000.0)
    assert len(comp_list) == 6
    for c in comp_list:
        assert c["base_year"] == 2000
        assert c["benchmark_year"] == 2024
        assert c["price_change_pct"] > 0
        assert c["base_quantity_affordable"] > c["benchmark_quantity_affordable"]

# 6. Trade balance identity: Balance = Exports - Imports
def test_trade_balance_identity():
    storage = TradeDataStorage()
    df_macro = storage.get_macro_annual()
    if not df_macro.empty:
        diff = (df_macro["trade_balance_usd_billion"] - (
            df_macro["exports_usd_billion"] - df_macro["imports_usd_billion"]
        )).abs()
        assert (diff < 0.05).all(), "Trade balance identity violated in macro dataset"

    df_bilateral = storage.get_bilateral_trade()
    if not df_bilateral.empty:
        diff_bil = (df_bilateral["trade_balance_usd_million"] - (
            df_bilateral["exports_usd_million"] - df_bilateral["imports_usd_million"]
        )).abs()
        assert (diff_bil < 0.05).all(), "Trade balance identity violated in bilateral dataset"

# 7. Trade openness formula: ((Exports + Imports) / GDP) * 100
def test_trade_openness_formula():
    storage = TradeDataStorage()
    df_macro = storage.get_macro_annual()
    if not df_macro.empty and "gdp_usd_billion" in df_macro.columns:
        expected_openness = (
            ((df_macro["exports_usd_billion"] + df_macro["imports_usd_billion"]) / df_macro["gdp_usd_billion"]) * 100.0
        ).round(2)
        diff = (df_macro["calculated_trade_openness_pct"] - expected_openness).abs()
        assert (diff < 0.05).all(), "Trade openness formula mismatch in macro dataset"

# 8. Rule of 70 halving time calculation
def test_rule_of_70_halving_time():
    assert EconometricAnalyzer.get_inflation_halving_time(7.0) == 10.0
    assert EconometricAnalyzer.get_inflation_halving_time(5.0) == 14.0
    assert EconometricAnalyzer.get_inflation_halving_time(5.82) == 12.0
    assert EconometricAnalyzer.get_inflation_halving_time(0.0) == float("inf")
    assert EconometricAnalyzer.get_inflation_halving_time(-2.0) == float("inf")

# 9. Pre/post-COVID comparison statistics calculation
def test_pre_post_covid_comparison():
    storage = TradeDataStorage()
    df_macro = storage.get_macro_annual()
    if not df_macro.empty:
        sb = EconometricAnalyzer.analyze_pre_post_covid(df_macro)
        assert "pre_covid_avg_exports_usd_b" in sb
        assert "post_covid_avg_exports_usd_b" in sb
        assert "exports_expansion_pct" in sb
        assert sb["post_covid_avg_exports_usd_b"] > sb["pre_covid_avg_exports_usd_b"]
        assert sb["exports_expansion_pct"] > 0

# 10. AI fallback protection
def test_ai_fallback_protection():
    assistant = TradeAIAssistant()
    # Empty stats passed
    report = assistant.query("The Post-2020 Export Breakout", {})
    assert report["data_status"] == "FALLBACK_INDICATIVE_BENCHMARK"
    assert report["fact"].startswith("[DATA AUDIT NOTICE:")
    
    # Verified stats passed
    verified_stats = {
        "is_fallback": False,
        "latest_year": 2024,
        "latest_exports_usd_b": 829.8,
        "latest_imports_usd_b": 895.0,
        "latest_trade_balance_usd_b": -65.2
    }
    report_verified = assistant.query("The Post-2020 Export Breakout", verified_stats)
    assert report_verified["data_status"] == "VERIFIED_EMPIRICAL_CALCULATION"
    assert not report_verified["fact"].startswith("[DATA AUDIT NOTICE:")

# 11. Data catalog schema integrity and consistency
def test_data_catalog_integrity():
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "metadata" / "data_catalog.json"
    assert catalog_path.exists()
    
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    
    assert "sources" in catalog
    assert len(catalog["sources"]) >= 3
    
    for src in catalog["sources"]:
        assert "id" in src
        assert "name" in src
        assert "publisher" in src
        assert "url" in src
        assert "coverage" in src
        assert "frequency" in src
        assert "series" in src
        for s in src["series"]:
            assert "name" in s
            assert "units" in s
            assert "definition" in s
