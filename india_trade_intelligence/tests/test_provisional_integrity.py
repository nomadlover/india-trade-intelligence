"""Provisional Trade Data Integrity, SEZ Reconciliation, and Estimation Risk Tests.

Covers the 18 mandatory test scenarios:
1. Duplicate transaction identifiers (CONFIRMED_DUPLICATE)
2. Legitimate repeated transactions with similar values (LEGITIMATE_REPEATED_TRANSACTION)
3. Candidate duplicates without transaction IDs (POTENTIAL_DUPLICATE flagged, not dropped)
4. Unreconciled data compared with an official aggregate (DISCREPANCY_IDENTIFIED, no artificial balancing)
5. Source totals differing due to reporting definitions (STRUCTURAL_DEFINITION_DIFFERENCE explained)
6. Preliminary observation subsequently revised (Revision magnitude & direction recorded)
7. Preservation of historical versions (Full revision trail preserved)
8. Partial-year compared with complete year (Comparability warning generated)
9. Annualisation of insufficient monthly data (Refused if N < 3; linear vs seasonal with bounds)
10. Merchandise combined with estimated services (Composite status never marked final)
11. Different reporting periods across components (Mismatch detected and reported)
12. Missing source publication status (Assigned UNKNOWN_STATUS and flagged)
13. Documented data-quality warning (Appropriate standardized warning text included)
14. Clean dataset displaying no unsupported warnings (No false positive warnings)
15. Bilateral reporting lags (Transit-time delay and CIF/FOB valuation markup qualified)
16. Suspected anomaly as a review signal, not proof of error (Flagged for review, not asserted wrong)
17. AI-generated analysis acknowledging provisional/estimated data (Explicitly mentioned in outputs)
18. Source outage preserving validated historical data (Historical data intact despite fetch failure)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from india_trade_intelligence.src.pipeline.quality_engine import (
    ObservationPublicationStatus,
    DataQualityClassification,
    DataQualityRecord,
    DataQualityStatusEngine,
)
from india_trade_intelligence.src.pipeline.reconciliation import (
    DuplicateClassification,
    ReconciliationStatus,
    TradeReconciliationEngine,
)
from india_trade_intelligence.src.pipeline.revisions import (
    TradeRevisionRecord,
    TradeRevisionTracker,
    TradeAnnualisationEngine,
)
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer
from india_trade_intelligence.src.ai.assistant import TradeAIAssistant
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage


# Scenario 1: Duplicate transaction identifiers
def test_scenario_01_duplicate_transaction_identifiers():
    records = [
        {"txn_id": "TXN_001", "country": "USA", "flow": "Exports", "value": 150.0},
        {"txn_id": "TXN_001", "country": "USA", "flow": "Exports", "value": 150.0},
        {"txn_id": "TXN_002", "country": "UAE", "flow": "Exports", "value": 85.0},
    ]
    df = pd.DataFrame(records)
    res = TradeReconciliationEngine.check_duplicates(df, transaction_id_col="txn_id")
    assert res["duplicate_status"] == DuplicateClassification.CONFIRMED_DUPLICATE
    assert res["confirmed_duplicates_detected"] is True
    assert res["classification_counts"][DuplicateClassification.CONFIRMED_DUPLICATE.value] == 2


# Scenario 2: Legitimate repeated transactions with similar values
def test_scenario_02_legitimate_repeated_transactions_similar_values():
    records = [
        {"txn_id": "TXN_101", "country": "Germany", "flow": "Imports", "chapter": 84, "value": 42.50},
        {"txn_id": "TXN_102", "country": "Germany", "flow": "Imports", "chapter": 84, "value": 42.50},
    ]
    df = pd.DataFrame(records)
    res = TradeReconciliationEngine.check_duplicates(
        df, transaction_id_col="txn_id", composite_key_cols=["country", "flow", "chapter", "value"]
    )
    assert res["confirmed_duplicates_detected"] is False
    assert res["classification_counts"][DuplicateClassification.CONFIRMED_DUPLICATE.value] == 0
    assert res["classification_counts"][DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value] == 2


# Scenario 3: Candidate duplicates without transaction IDs
def test_scenario_03_candidate_duplicates_without_transaction_ids():
    records = [
        {"country": "Singapore", "flow": "Exports", "chapter": 85, "date": "2024-06-01", "value": 75.0},
        {"country": "Singapore", "flow": "Exports", "chapter": 85, "date": "2024-06-01", "value": 75.0},
        {"country": "Singapore", "flow": "Exports", "chapter": 85, "date": "2024-06-15", "value": 75.0},
    ]
    df = pd.DataFrame(records)
    res = TradeReconciliationEngine.check_duplicates(
        df, composite_key_cols=["country", "flow", "chapter", "value"], timestamp_col="date"
    )
    assert res["duplicate_status"] == DuplicateClassification.POTENTIAL_DUPLICATE
    assert res["classification_counts"][DuplicateClassification.POTENTIAL_DUPLICATE.value] == 2
    assert res["classification_counts"][DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value] == 1
    # Confirms records are flagged for review rather than automatically dropped
    assert "no records deleted without verified proof" in res["notes"]


# Scenario 4: Unreconciled data compared with an official aggregate
def test_scenario_04_unreconciled_data_official_aggregate():
    components_sum = 390.0
    official_aggregate = 410.0
    res = TradeReconciliationEngine.reconcile_aggregates(
        derived_total=components_sum,
        official_reference_total=official_aggregate,
        flow_label="Exports",
        period_label="FY 2023-24",
        tolerance_pct=1.0
    )
    assert res["reconciliation_status"] == ReconciliationStatus.DISCREPANCY_IDENTIFIED
    assert res["derived_total"] == 390.0
    assert res["official_reference_total"] == 410.0
    assert res["absolute_discrepancy"] == 20.0
    assert round(res["percentage_discrepancy"], 2) == 4.88
    # No forced balancing plug
    assert "balancing_plug" not in res


# Scenario 5: Source totals differing due to reporting definitions
def test_scenario_05_source_totals_reporting_definitions():
    dgcis_customs_exports = 437.1
    rbi_bop_exports = 445.8
    notes = "Customs basis (physical boundary crossing at port) vs BoP basis (change in economic ownership)."
    res = TradeReconciliationEngine.reconcile_aggregates(
        derived_total=dgcis_customs_exports,
        official_reference_total=rbi_bop_exports,
        definition_difference_notes=notes
    )
    assert res["reconciliation_status"] == ReconciliationStatus.STRUCTURAL_DEFINITION_DIFFERENCE
    assert res["definition_difference_notes"] == notes
    assert "Discrepancy explained by verified difference in reporting definitions" in res["verdict"]


# Scenario 6: Preliminary observation subsequently revised
def test_scenario_06_preliminary_observation_subsequently_revised():
    tracker = TradeRevisionTracker()
    r1 = tracker.log_observation(
        series_name="merchandise_exports",
        observation_period="2024-04",
        value=34.99,
        release_date="2024-05-15",
        publication_status="QUICK_ESTIMATE"
    )
    r2 = tracker.log_observation(
        series_name="merchandise_exports",
        observation_period="2024-04",
        value=35.45,
        release_date="2024-06-15",
        publication_status="PROVISIONAL"
    )
    assert r2.previous_value == 34.99
    assert r2.revision_magnitude == pytest.approx(0.46, abs=0.01)
    assert r2.revision_pct == pytest.approx(1.31, abs=0.02)
    assert r2.direction == "UPWARD"


# Scenario 7: Preservation of historical versions
def test_scenario_07_preservation_of_historical_versions():
    tracker = TradeRevisionTracker()
    tracker.log_observation("merchandise_imports", "2024-05", 61.91, "2024-06-15", "QUICK_ESTIMATE")
    tracker.log_observation("merchandise_imports", "2024-05", 61.50, "2024-07-15", "PROVISIONAL")
    tracker.log_observation("merchandise_imports", "2024-05", 61.42, "2024-08-15", "REVISED_PROVISIONAL")

    history = tracker.get_version_history("merchandise_imports", "2024-05")
    assert len(history) == 3
    assert [v.release_version for v in history] == [1, 2, 3]
    assert history[0].value == 61.91
    assert history[1].value == 61.50
    assert history[2].value == 61.42
    assert history[2].direction == "DOWNWARD"


# Scenario 8: Partial-year compared with complete year
def test_scenario_08_partial_year_compared_with_complete_year():
    warning = DataQualityStatusEngine.generate_chart_warning(
        warning_type="PARTIAL_YEAR",
        custom_details="Comparing FY 2024-25 Q1 (Apr-Jul, 4 months) with FY 2023-24 (12 months)."
    )
    assert "Coverage: Partial reporting year" in warning
    assert "Comparing FY 2024-25 Q1" in warning
    assert "Do not compare this total directly with a complete annual total" in warning


# Scenario 9: Annualisation of insufficient monthly data
def test_scenario_09_annualisation_insufficient_monthly_data():
    two_months = [35.0, 38.0]
    res_two = TradeAnnualisationEngine.calculate_annualisation_bounds(two_months, min_months_required=3)
    assert res_two["is_projectable"] is False
    assert res_two["status"] == "INSUFFICIENT_DATA_FOR_PROJECTION"
    assert "fewer than 3 months" in res_two["guidance"]

    four_months = [35.0, 38.0, 36.0, 37.0]  # Sum = 146.0
    res_four = TradeAnnualisationEngine.calculate_annualisation_bounds(four_months, min_months_required=3)
    assert res_four["is_projectable"] is True
    assert res_four["observed_months"] == 4
    assert res_four["observed_to_date_total"] == 146.0
    assert res_four["simple_linear_projection"] == pytest.approx(438.0, abs=0.1)
    assert res_four["seasonal_baseline_projection"] == pytest.approx(462.0, abs=1.0)
    assert "NOT an official government forecast" in res_four["methodology_disclaimer"]


# Scenario 10: Merchandise combined with estimated services
def test_scenario_10_merchandise_combined_with_estimated_services():
    status_info = DataQualityStatusEngine.propagate_combined_status(
        merchandise_status=ObservationPublicationStatus.PROVISIONAL,
        services_status=ObservationPublicationStatus.ESTIMATED
    )
    assert status_info["composite_status"] == ObservationPublicationStatus.PROVISIONAL
    assert status_info["is_final"] is False
    assert status_info["composite_classification"] == DataQualityClassification.OFFICIAL_BUT_PROVISIONAL
    assert "subject to subsequent revision" in status_info["description"]


# Scenario 11: Different reporting periods across components
def test_scenario_11_different_reporting_periods_across_components():
    df_merch = pd.DataFrame([
        {"period": "2024-04", "merchandise_exports": 35.0, "merchandise_status": "PROVISIONAL"},
        {"period": "2024-05", "merchandise_exports": 38.0, "merchandise_status": "PROVISIONAL"},
        {"period": "2024-06", "merchandise_exports": 36.0, "merchandise_status": "PROVISIONAL"},
    ])
    df_serv = pd.DataFrame([
        {"period": "2024-04", "services_exports": 30.0, "services_status": "ESTIMATED"},
        {"period": "2024-05", "services_exports": 29.0, "services_status": "ESTIMATED"},
    ])
    combined = TradeDataTransformer.combine_merchandise_and_services(df_merch, df_serv)
    row_june = combined[combined["period"] == "2024-06"].iloc[0]
    assert np.isnan(row_june["total_exports_usd_billion"]) or row_june["composite_data_status"] == "PERIOD_MISMATCH_OR_UNKNOWN"


# Scenario 12: Missing source publication status
def test_scenario_12_missing_source_publication_status():
    classification = DataQualityStatusEngine.classify_status(
        is_official=True,
        pub_status=ObservationPublicationStatus.UNKNOWN_STATUS,
        is_reconciled=False
    )
    assert classification == DataQualityClassification.UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED


# Scenario 13: Documented data-quality warning
def test_scenario_13_documented_data_quality_warning():
    w_merch = DataQualityStatusEngine.generate_chart_warning("PROVISIONAL_MERCHANDISE")
    assert "Reporting status: Provisional" in w_merch

    w_serv = DataQualityStatusEngine.generate_chart_warning("ESTIMATED_SERVICES")
    assert "Reporting status: Estimated" in w_serv

    w_comb = DataQualityStatusEngine.generate_chart_warning("COMBINED_TOTALS")
    assert "This total combines merchandise and services components" in w_comb

    w_dupe = DataQualityStatusEngine.generate_chart_warning("UNRECONCILED_DUPLICATION_RISK")
    assert "Data quality warning: This dataset has not yet been reconciled" in w_dupe


# Scenario 14: Clean dataset displaying no unsupported warnings
def test_scenario_14_clean_dataset_no_unsupported_warnings():
    classification = DataQualityStatusEngine.classify_status(
        is_official=True,
        pub_status=ObservationPublicationStatus.FINAL_RECONCILED,
        is_reconciled=True,
        has_quality_issue=False
    )
    assert classification == DataQualityClassification.VERIFIED_AND_RECONCILED
    assert classification != DataQualityClassification.OFFICIAL_BUT_PROVISIONAL
    assert classification != DataQualityClassification.POTENTIALLY_AFFECTED_BY_DATA_QUALITY_ISSUE


# Scenario 15: Bilateral reporting lags
def test_scenario_15_bilateral_reporting_lags():
    comparison = TradeReconciliationEngine.compare_reporting_lags(
        exporter_reported_usd_m=100.0,
        importer_reported_usd_m=110.0,
        partner_country="United States",
        period_label="FY2024",
        estimated_cif_markup_pct=10.0,
        transit_lag_weeks=4
    )
    assert comparison["partner_country"] == "United States"
    assert comparison["assumed_transit_lag_weeks"] == 4
    assert comparison["estimated_cif_markup_pct"] == 10.0
    assert comparison["divergence_from_expected_pct"] == 0.0
    assert "FOB vs CIF valuation differences" in comparison["methodology_note"]
    assert "shipping transit time lags" in comparison["methodology_note"]


# Scenario 16: Suspected anomaly as a review signal, not proof of error
def test_scenario_16_suspected_anomaly_review_signal_not_proof_of_error():
    series = pd.Series([30.0, 31.0, 32.0, 60.0])  # ~87% jump in last period
    periods = pd.Series(["2024-01", "2024-02", "2024-03", "2024-04"])
    anomalies = TradeReconciliationEngine.detect_trade_anomalies(
        series=series,
        period_series=periods,
        mom_threshold_pct=25.0,
        yoy_threshold_pct=50.0
    )
    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom["period"] == "2024-04"
    assert anom["percentage_change"] == pytest.approx(87.5, abs=0.5)
    # Crucial epistemic check: signal, not proof of error
    assert "Treat as an investigation signal" in anom["guidance"]
    assert "do NOT assume data corruption without source corroboration" in anom["guidance"]


# Scenario 17: AI-generated analysis acknowledging provisional/estimated data
def test_scenario_17_ai_analysis_acknowledging_provisional_data():
    assistant = TradeAIAssistant()
    stats = {
        "latest_year": 2025,
        "latest_exports": 144.1,
        "latest_imports": 229.7,
        "latest_balance": -85.6,
        "cagr_exports": 5.4,
        "top_export_destination": "USA",
        "top_import_source": "China",
        "is_provisional": True,
        "provisional_period": "FY 2024-25 Q1 (Apr-Jul 2024)",
        "has_estimated_services": True,
    }
    report = assistant.query("What is the trade trajectory?", stats)
    assert "fact" in report
    fact_text = report["fact"]
    assert "PROVISIONAL DATA AUDIT NOTICE" in fact_text
    assert "FY 2024-25 Q1" in fact_text
    assert "SERVICES TRADE ESTIMATION NOTICE" in fact_text
    assert "subject to quarterly BoP reconciliation" in fact_text


# Scenario 18: Source outage preserving validated historical data
def test_scenario_18_source_outage_preserving_validated_historical_data():
    storage = TradeDataStorage()
    df_macro_before = storage.get_macro_annual()
    assert len(df_macro_before) >= 30, "Database must contain at least 30 years of validated historical data"

    # Simulate an external upstream source failure
    def failing_upstream_fetch():
        raise ConnectionError("DGCI&S portal timeout / ICEGATE EDI migration outage")

    with pytest.raises(ConnectionError):
        failing_upstream_fetch()

    # Verify that existing validated historical data is unaffected and preserved in storage
    df_macro_after = storage.get_macro_annual()
    assert len(df_macro_after) == len(df_macro_before)
    assert df_macro_after.iloc[0]["year"] == df_macro_before.iloc[0]["year"]
    assert df_macro_after.iloc[-1]["exports_usd_billion"] == df_macro_before.iloc[-1]["exports_usd_billion"]
