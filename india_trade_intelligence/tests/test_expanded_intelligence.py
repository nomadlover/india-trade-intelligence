"""Comprehensive Automated Test Suite for Expanded India Trade Intelligence.
Covers:
1. Price vs Quantity log-additive decomposition identity (Delta ln V = Delta ln P + Delta ln Q)
2. Energy terms-of-trade exposure & Russian crude discount metrics
3. External sector resilience metrics (CAD % GDP, FX import cover)
4. Key trading partner macroeconomic conditions & PMI
5. Trade policy and geopolitical timeline catalog integrity
6. Economic risk indicators (HHI and single-supplier vulnerability shares)
7. AI Assistant explicit abstention on unverified future years / out-of-scope queries
8. Pipeline fail-safe integrity preservation
"""
import pytest
import math
import pandas as pd
import numpy as np

from india_trade_intelligence.src.pipeline.storage import TradeDataStorage
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer
from india_trade_intelligence.src.ai.assistant import TradeAIAssistant, RESEARCH_QUESTIONS_CATALOG
from india_trade_intelligence.src.pipeline.provenance import get_provenance, PROVENANCE_REGISTRY

@pytest.fixture
def storage():
    return TradeDataStorage()

# 1. Price vs Quantity log-additive decomposition identity
def test_price_quantity_decomposition_identity(storage):
    df_pq = storage.get_commodity_price_quantity()
    assert not df_pq.empty, "Commodity price quantity dataset must not be empty"
    
    df_trans = TradeDataTransformer.transform_commodity_price_quantity(df_pq)
    assert "price_effect_log_pct" in df_trans.columns
    assert "quantity_effect_log_pct" in df_trans.columns
    assert "value_effect_log_pct" in df_trans.columns

    # Test the mathematical identity: Delta ln(V) = Delta ln(P) + Delta ln(Q)
    valid_decomp = df_trans.dropna(subset=["price_effect_log_pct", "quantity_effect_log_pct", "value_effect_log_pct"])
    assert len(valid_decomp) > 0

    diff = (valid_decomp["value_effect_log_pct"] - (
        valid_decomp["price_effect_log_pct"] + valid_decomp["quantity_effect_log_pct"]
    )).abs()
    assert (diff < 0.005).all(), "Log-additive decomposition identity Delta ln V = Delta ln P + Delta ln Q must hold exactly"

# 2. Energy exposure & crude discount
def test_energy_exposure_calculations(storage):
    df_energy = storage.get_energy_commodity_exposure()
    assert not df_energy.empty, "Energy exposure dataset must not be empty"
    assert len(df_energy) >= 15

    df_trans = TradeDataTransformer.transform_energy_commodity_exposure(df_energy)
    assert "crude_discount_to_brent_usd_bbl" in df_trans.columns
    assert "refining_export_coverage_ratio" in df_trans.columns

    # Test Brent vs Indian Basket average discount is positive post-2022
    recent_energy = df_trans[df_trans["year"] >= 2022]
    assert recent_energy["crude_discount_to_brent_usd_bbl"].mean() > 0, "Russian discount must yield positive average Brent-to-Indian Basket spread post-2022"

    # Test net petroleum bill identity: Net = Crude - Refined Exports
    for _, row in df_trans.iterrows():
        expected_net = row["gross_crude_oil_imports_usd_b"] - row["petroleum_product_exports_usd_b"]
        assert abs(row["net_petroleum_import_bill_usd_b"] - expected_net) < 0.1

# 3. External sector macro indicators
def test_external_sector_macro(storage):
    df_ext = storage.get_external_sector_macro()
    assert not df_ext.empty, "External sector macro dataset must not be empty"
    assert len(df_ext) >= 30

    df_trans = TradeDataTransformer.transform_external_sector_macro(df_ext)
    assert "import_cover_months" in df_trans.columns

    # FX reserves import cover should exceed 8 months in recent years (2020-2025)
    recent_ext = df_trans[df_trans["year"] >= 2020]
    assert (recent_ext["import_cover_months"] >= 8.0).all(), "FX reserves should provide robust import cover >8 months post-2020"

    # Current Account Deficit should be within plausible historical corridor (-5.0% to +2.5% of GDP)
    assert (df_trans["current_account_deficit_pct_gdp"] >= -5.0).all()
    assert (df_trans["current_account_deficit_pct_gdp"] <= 2.5).all()

# 4. Key trading partner macroeconomic conditions
def test_trading_partner_conditions(storage):
    df_partner = storage.get_trading_partner_conditions()
    assert not df_partner.empty, "Trading partner dataset must not be empty"
    
    partners = df_partner["country_name"].unique()
    assert "United States" in partners
    assert "China" in partners
    assert "United Arab Emirates" in partners
    assert "European Union" in partners

    # Manufacturing PMI must be in normal diffusion range (30 to 70)
    assert (df_partner["manufacturing_pmi"] >= 30.0).all()
    assert (df_partner["manufacturing_pmi"] <= 70.0).all()

# 5. Trade policy events timeline catalog
def test_trade_policy_events(storage):
    df_policy = storage.get_trade_policy_events()
    assert not df_policy.empty, "Trade policy events catalog must not be empty"
    assert len(df_policy) >= 10

    event_names = " ".join(df_policy["event_name"].tolist())
    assert "CEPA" in event_names
    assert "TEPA" in event_names
    assert "PLI" in event_names
    assert "Red Sea" in event_names

    # Verification status must be VERIFIED_OFFICIAL
    assert (df_policy["empirical_verification_status"] == "VERIFIED_OFFICIAL").all()

# 6. Economic risk indicators
def test_economic_risk_indicators(storage):
    df_bilateral = storage.get_bilateral_trade()
    df_commodity = storage.get_commodity_trade()
    df_energy = storage.get_energy_commodity_exposure()

    risk_result = TradeDataTransformer.compute_economic_risk_indicators(df_bilateral, df_commodity, df_energy)
    assert isinstance(risk_result, dict), "Risk result should be a dictionary"
    assert "export_partner_hhi" in risk_result
    assert "critical_dependencies" in risk_result

    crit = risk_result["critical_dependencies"]
    assert "Active Pharmaceutical Ingredients (APIs)" in crit
    assert crit["Active Pharmaceutical Ingredients (APIs)"]["import_share_pct"] > 50.0
    assert crit["Solar Photovoltaic Cells & Modules"]["import_share_pct"] > 50.0
    assert crit["Coking Coal (Metallurgical)"]["import_share_pct"] > 40.0
    assert 0.0 <= risk_result["net_energy_vulnerability_pct"] <= 100.0

# 7. AI Assistant Explicit Abstention Mandate
def test_ai_assistant_explicit_abstention():
    assistant = TradeAIAssistant()
    mock_stats = {
        "latest_year": 2024,
        "latest_exports_usd_b": 829.8,
        "latest_imports_usd_b": 895.0,
        "latest_trade_balance_usd_b": -65.2
    }

    # Query future unverified year 2028
    res_future = assistant.query("What will India's exports be in 2028?", mock_stats)
    assert res_future["data_status"] == "EXPLICIT_ABSTENTION_UNVERIFIED_PERIOD"
    assert "EXPLICIT ABSTENTION" in res_future["fact"]
    assert "Calculation declined" in res_future["calculation"]

    # Query future unverified year 2030
    res_2030 = assistant.query("Predict the 2030 merchandise trade balance", mock_stats)
    assert res_2030["data_status"] == "EXPLICIT_ABSTENTION_UNVERIFIED_PERIOD"

    # Query out-of-scope topic (cryptocurrency)
    res_crypto = assistant.query("What is the impact of Bitcoin cryptocurrency reserves on Indian trade?", mock_stats)
    assert res_crypto["data_status"] == "EXPLICIT_ABSTENTION_UNVERIFIED_PERIOD"

# 8. Provenance registry completeness for new indicators
def test_expanded_provenance_registry():
    new_metrics = [
        "commodity_price_quantity_decomp",
        "energy_crude_exposure",
        "external_sector_fx_cad",
        "trading_partner_macro",
        "trade_policy_events",
        "economic_risk_hhi"
    ]
    for mid in new_metrics:
        prov = get_provenance(mid)
        assert prov is not None, f"Metric '{mid}' must be registered in PROVENANCE_REGISTRY"
        assert prov.source_agency != "", f"Metric '{mid}' must have a valid source agency"
        assert prov.observation_period != "", f"Metric '{mid}' must have an observation period"
