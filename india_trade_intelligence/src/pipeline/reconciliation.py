"""SEZ-ICEGATE Reconciliation, Duplicate Detection, and Anomaly Analysis Module.
Handles customs reporting systems (DGCI&S, ICEGATE, SEZ Online, DTA clearances),
composite-key duplicate classification, aggregate reconciliation against reference totals,
anomaly detection review signals, and reporting-lag comparisons.
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

class DuplicateClassification(str, Enum):
    """Rigorous classification for duplicate detection under customs reporting."""
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE"
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"
    LEGITIMATE_REPEATED_TRANSACTION = "LEGITIMATE_REPEATED_TRANSACTION"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE_AGGREGATE_LEVEL = "NOT_APPLICABLE_AGGREGATE_LEVEL"

class ReconciliationStatus(str, Enum):
    """Outcome status of aggregate reconciliation."""
    RECONCILED_WITHIN_TOLERANCE = "RECONCILED_WITHIN_TOLERANCE"
    DISCREPANCY_IDENTIFIED = "DISCREPANCY_IDENTIFIED"
    UNRECONCILED_MISSING_REFERENCE = "UNRECONCILED_MISSING_REFERENCE"
    STRUCTURAL_DEFINITION_DIFFERENCE = "STRUCTURAL_DEFINITION_DIFFERENCE"

class TradeReconciliationEngine:
    """Executes research-grade reconciliation, deduplication, and anomaly audits."""

    @staticmethod
    def get_sez_reporting_methodology() -> Dict[str, Any]:
        """Provides documented methodology on SEZ, ICEGATE, and DTA reporting in India.
        
        Source Basis: DGCI&S Methodology Notes, Ministry of Commerce SEZ Rules 2006,
        and CBIC ICEGATE Electronic Gateway migration circulars.
        """
        return {
            "originating_systems": {
                "ICEGATE": "Indian Customs Electronic Gateway for EDI declarations (bills of entry and shipping bills).",
                "SEZ_Online": "Dedicated system administered by Ministry of Commerce for SEZ units and developers.",
                "DGCIS": "Directorate General of Commercial Intelligence and Statistics; aggregates national foreign trade statistics."
            },
            "sez_aggregate_inclusion": (
                "Official DGCI&S national merchandise trade aggregates INCLUDE exports and imports by Special Economic Zone (SEZ) units. "
                "Physical merchandise crossing international borders from SEZs is treated as national exports; foreign goods entering SEZs are treated as national imports."
            ),
            "dta_clearance_treatment": (
                "Domestic Tariff Area (DTA) sales: When an SEZ unit sells goods into the DTA (domestic market within India), "
                "the transaction requires an import bill of entry for customs duties. However, in national balance-of-payments "
                "and foreign trade statistics, DTA sales represent domestic inter-zone movements and are NOT counted as international trade."
            ),
            "icegate_sez_migration_risk": (
                "Risk scenario: During phased migration of SEZ declarations onto ICEGATE EDI, temporary duplicate records can arise "
                "if transactions are filed on both SEZ Online and ICEGATE without cross-system deduplication. "
                "Statistical aggregates must be verified to ensure such transactions are not double counted."
            )
        }

    @staticmethod
    def check_duplicates(
        df: pd.DataFrame,
        transaction_id_col: Optional[str] = None,
        composite_key_cols: Optional[List[str]] = None,
        timestamp_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """Audits candidate duplicates using transaction identifiers or composite keys.
        
        Classifies records into 5 distinct categories:
        1. CONFIRMED_DUPLICATE: Identical transaction identifier with duplicate filing.
        2. POTENTIAL_DUPLICATE: Matching composite key (period, partner, commodity, value) without unique ID to disambiguate.
        3. LEGITIMATE_REPEATED_TRANSACTION: Matching composite key but verified distinct timestamps or shipping bill numbers.
        4. UNRESOLVED: Ambiguous records during migration window.
        5. NOT_APPLICABLE_AGGREGATE_LEVEL: Dataset is aggregated; transaction-level deduplication is not supported.
        """
        if df.empty:
            return {
                "total_records": 0,
                "classification_counts": {},
                "duplicate_status": DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL,
                "notes": "Empty dataset provided."
            }

        # If data has no transaction identifiers and only high-level aggregates
        if not transaction_id_col and (not composite_key_cols or len(df.columns) < 4):
            return {
                "total_records": len(df),
                "classification_counts": {DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL.value: len(df)},
                "duplicate_status": DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL,
                "notes": (
                    "DATA LIMITATION: The dataset is aggregated at the national, partner, or commodity-chapter level. "
                    "Transaction-level duplicate detection cannot be evaluated on aggregated totals. Limitation is documented explicitly."
                )
            }

        counts = {
            DuplicateClassification.CONFIRMED_DUPLICATE.value: 0,
            DuplicateClassification.POTENTIAL_DUPLICATE.value: 0,
            DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value: 0,
            DuplicateClassification.UNRESOLVED.value: 0,
            DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL.value: 0
        }

        # 1. Transaction ID evaluation
        if transaction_id_col and transaction_id_col in df.columns:
            duplicated_ids = df[df.duplicated(subset=[transaction_id_col], keep=False)]
            confirmed_dup_count = len(duplicated_ids)
            counts[DuplicateClassification.CONFIRMED_DUPLICATE.value] = confirmed_dup_count

            # If there are also repeated composite keys with distinct IDs
            if composite_key_cols and all(c in df.columns for c in composite_key_cols):
                unique_id_df = df.drop_duplicates(subset=[transaction_id_col])
                repeated_legit = unique_id_df[unique_id_df.duplicated(subset=composite_key_cols, keep=False)]
                counts[DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value] = len(repeated_legit)
            
            clean_count = len(df) - confirmed_dup_count - counts[DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value]
            dominant_status = (
                DuplicateClassification.CONFIRMED_DUPLICATE
                if confirmed_dup_count > 0
                else DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION
            )
            return {
                "total_records": len(df),
                "classification_counts": counts,
                "duplicate_status": dominant_status,
                "confirmed_duplicates_detected": (confirmed_dup_count > 0),
                "notes": f"Evaluated {len(df)} records using transaction identifier '{transaction_id_col}'."
            }

        # 2. Composite key evaluation (when transaction IDs are unavailable)
        if composite_key_cols and all(c in df.columns for c in composite_key_cols):
            dup_mask = df.duplicated(subset=composite_key_cols, keep=False)
            potential_dup_records = df[dup_mask]
            potential_count = len(potential_dup_records)
            
            # If timestamp or date exists to disambiguate repeated legitimate shipments
            if timestamp_col and timestamp_col in df.columns and potential_count > 0:
                distinct_dates_mask = potential_dup_records.duplicated(subset=composite_key_cols + [timestamp_col], keep=False)
                counts[DuplicateClassification.POTENTIAL_DUPLICATE.value] = int(distinct_dates_mask.sum())
                counts[DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION.value] = potential_count - counts[DuplicateClassification.POTENTIAL_DUPLICATE.value]
            else:
                counts[DuplicateClassification.POTENTIAL_DUPLICATE.value] = potential_count

            dominant_status = (
                DuplicateClassification.POTENTIAL_DUPLICATE
                if counts[DuplicateClassification.POTENTIAL_DUPLICATE.value] > 0
                else DuplicateClassification.LEGITIMATE_REPEATED_TRANSACTION
            )

            return {
                "total_records": len(df),
                "classification_counts": counts,
                "duplicate_status": dominant_status,
                "confirmed_duplicates_detected": False,
                "notes": (
                    f"Evaluated {len(df)} records using composite key {composite_key_cols}. "
                    "Records sharing composite keys are classified as POTENTIAL_DUPLICATE or LEGITIMATE_REPEATED_TRANSACTION; "
                    "no records deleted without verified proof."
                )
            }

        return {
            "total_records": len(df),
            "classification_counts": {DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL.value: len(df)},
            "duplicate_status": DuplicateClassification.NOT_APPLICABLE_AGGREGATE_LEVEL,
            "notes": "Specified key columns not found in dataset."
        }

    @staticmethod
    def reconcile_aggregates(
        derived_total: float,
        official_reference_total: float,
        flow_label: str = "Exports",
        period_label: str = "Annual",
        tolerance_pct: float = 0.5,
        definition_difference_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compares derived micro/sectoral totals against official published reference totals.
        
        Preserves original data and quantifies discrepancies without forced balancing adjustments.
        """
        abs_diff = round(abs(derived_total - official_reference_total), 3)
        pct_diff = round((abs_diff / official_reference_total * 100.0), 3) if official_reference_total > 0 else 0.0

        if definition_difference_notes:
            status = ReconciliationStatus.STRUCTURAL_DEFINITION_DIFFERENCE
            verdict = "Discrepancy explained by verified difference in reporting definitions (e.g. Customs vs BoP, or SEZ inclusion)."
        elif pct_diff <= tolerance_pct:
            status = ReconciliationStatus.RECONCILED_WITHIN_TOLERANCE
            verdict = f"Derived total matches official reference total within acceptable statistical tolerance (±{tolerance_pct}%)."
        else:
            status = ReconciliationStatus.DISCREPANCY_IDENTIFIED
            verdict = f"Discrepancy of {pct_diff:.2f}% exceeds tolerance threshold ({tolerance_pct}%). Requires investigation."

        return {
            "flow_label": flow_label,
            "period_label": period_label,
            "derived_total": round(derived_total, 2),
            "official_reference_total": round(official_reference_total, 2),
            "absolute_discrepancy": abs_diff,
            "percentage_discrepancy": pct_diff,
            "tolerance_threshold_pct": tolerance_pct,
            "reconciliation_status": status,
            "verdict": verdict,
            "definition_difference_notes": definition_difference_notes
        }

    @staticmethod
    def detect_trade_anomalies(
        series: pd.Series,
        period_series: pd.Series,
        mom_threshold_pct: float = 25.0,
        yoy_threshold_pct: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Identifies statistical anomalies across time series trade data.
        
        RULE: An anomaly is a review signal requiring investigation, NOT proof of error, fraud, or duplicate records.
        """
        anomalies = []
        if len(series) < 2:
            return anomalies

        df = pd.DataFrame({"period": period_series, "value": series}).dropna().reset_index(drop=True)
        df["pct_change"] = (df["value"].pct_change() * 100.0).round(2)

        for i in range(1, len(df)):
            pct = df.loc[i, "pct_change"]
            val = df.loc[i, "value"]
            prev_val = df.loc[i - 1, "value"]
            per = df.loc[i, "period"]

            if abs(pct) >= mom_threshold_pct:
                anomalies.append({
                    "period": per,
                    "value": round(float(val), 2),
                    "previous_value": round(float(prev_val), 2),
                    "percentage_change": round(float(pct), 2),
                    "anomaly_type": "LARGE_PERIOD_CHANGE",
                    "signal_level": "WARNING" if abs(pct) >= yoy_threshold_pct else "REVIEW_SIGNAL",
                    "guidance": (
                        f"Observed movement ({pct:+.1f}%) exceeds threshold (±{mom_threshold_pct}%). "
                        "Treat as an investigation signal; do NOT assume data corruption without source corroboration."
                    )
                })

        return anomalies

    @staticmethod
    def compare_reporting_lags(
        exporter_reported_usd_m: float,
        importer_reported_usd_m: float,
        partner_country: str,
        period_label: str = "FY2024",
        estimated_cif_markup_pct: float = 10.0,
        transit_lag_weeks: int = 4
    ) -> Dict[str, Any]:
        """Evaluates bilateral trade mirror statistics accounting for valuation methods and transit lags.
        
        Background:
          - Exporter statistics are recorded FOB (Free On Board) at shipment port.
          - Importer statistics are recorded CIF (Cost, Insurance, Freight) at arrival port.
          - Shipment transit time causes goods exported in month t to be recorded in month t+1 by importer.
        """
        # Expected importer value after CIF margin (CIF ≈ FOB * 1.10)
        expected_importer_val = exporter_reported_usd_m * (1.0 + (estimated_cif_markup_pct / 100.0))
        divergence_from_expected_pct = (
            ((importer_reported_usd_m - expected_importer_val) / expected_importer_val) * 100.0
            if expected_importer_val > 0 else 0.0
        )

        return {
            "partner_country": partner_country,
            "period": period_label,
            "exporter_fob_reported_usd_m": round(exporter_reported_usd_m, 2),
            "importer_cif_reported_usd_m": round(importer_reported_usd_m, 2),
            "estimated_cif_markup_pct": estimated_cif_markup_pct,
            "assumed_transit_lag_weeks": transit_lag_weeks,
            "expected_cif_value_usd_m": round(expected_importer_val, 2),
            "divergence_from_expected_pct": round(divergence_from_expected_pct, 2),
            "methodology_note": (
                "Bilateral mirror trade divergence arises naturally from: (1) FOB vs CIF valuation differences (~8-12% freight/insurance), "
                "(2) shipping transit time lags (2-6 weeks), and (3) merchanting/entrepôt trade through third countries. "
                "Discrepancies do not necessarily imply statistical reporting errors."
            )
        }
