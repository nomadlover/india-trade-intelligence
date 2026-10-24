"""Automated test suite for Module C: Data Revision Observatory."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from india_trade_intelligence.src.analysis.revisions import (
    DataRevisionObservatory,
    RevisionClassification,
    ObservationSnapshot
)
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage


class TestDataRevisionObservatory:
    """Verifies observation snapshotting, revision detection, classification, and alert triggers."""

    def test_generate_observation_key_deterministic(self):
        """Validates deterministic observation key generation across runs."""
        k1 = DataRevisionObservatory.generate_observation_key(
            dataset_id="dgcis_bilateral",
            reporting_period="2023-24",
            indicator_id="merchandise_exports_usd_billion",
            partner_country="USA",
            trade_flow="Export"
        )
        k2 = DataRevisionObservatory.generate_observation_key(
            dataset_id="DGCIS_BILATERAL",
            reporting_period=" 2023-24 ",
            indicator_id="MERCHANDISE_EXPORTS_USD_BILLION",
            partner_country="usa",
            trade_flow="export"
        )
        assert k1 == k2
        assert k1 == "dgcis_bilateral:2023-24:USA:export:merchandise_exports_usd_billion"

    def test_compare_snapshot_versions_identical(self):
        """Zero revisions detected when identical snapshot versions are compared."""
        rows = [
            {
                "observation_key": "macro:2023:exp",
                "dataset_id": "macro_annual",
                "indicator_id": "exports",
                "reporting_period": "2023",
                "normalised_value": 437.10,
                "data_status": "FINAL",
                "normalised_unit": "USD_BILLION",
                "source_release_date": "2024-04-15"
            }
        ]
        df = pd.DataFrame(rows)
        comp = DataRevisionObservatory.compare_snapshot_versions(
            df_prev=df, df_new=df, prev_version_id="v1.0", new_version_id="v1.0-duplicate"
        )
        assert comp["summary"]["unchanged_count"] == 1
        assert comp["summary"]["revised_count"] == 0
        assert comp["summary"]["added_count"] == 0
        assert comp["summary"]["removed_count"] == 0
        assert len(comp["revisions"]) == 0

    def test_compare_snapshot_versions_added_and_removed(self):
        """Correctly identifies new observations and dropped observations."""
        prev_rows = [
            {"observation_key": "k1", "dataset_id": "d1", "indicator_id": "i1", "reporting_period": "p1", "normalised_value": 10.0, "data_status": "FINAL"},
            {"observation_key": "k2", "dataset_id": "d1", "indicator_id": "i2", "reporting_period": "p1", "normalised_value": 20.0, "data_status": "FINAL"}
        ]
        new_rows = [
            {"observation_key": "k2", "dataset_id": "d1", "indicator_id": "i2", "reporting_period": "p1", "normalised_value": 20.0, "data_status": "FINAL"},
            {"observation_key": "k3", "dataset_id": "d1", "indicator_id": "i3", "reporting_period": "p2", "normalised_value": 30.0, "data_status": "PROVISIONAL"}
        ]
        comp = DataRevisionObservatory.compare_snapshot_versions(
            df_prev=pd.DataFrame(prev_rows),
            df_new=pd.DataFrame(new_rows),
            prev_version_id="v1",
            new_version_id="v2"
        )
        assert comp["summary"]["added_count"] == 1
        assert comp["summary"]["removed_count"] == 1
        assert comp["summary"]["unchanged_count"] == 1
        assert comp["added"][0]["observation_key"] == "k3"
        assert comp["removed"][0]["observation_key"] == "k1"

    def test_revision_mathematics_and_safe_zero(self):
        """Verifies absolute revision and safe percentage revision calculation without ZeroDivisionError."""
        prev_rows = [
            {"observation_key": "k_normal", "dataset_id": "d1", "indicator_id": "exp", "reporting_period": "2023-24", "normalised_value": 100.0, "data_status": "PROVISIONAL"},
            {"observation_key": "k_zero", "dataset_id": "d1", "indicator_id": "exp", "reporting_period": "2023-24", "normalised_value": 0.0, "data_status": "PROVISIONAL"}
        ]
        new_rows = [
            {"observation_key": "k_normal", "dataset_id": "d1", "indicator_id": "exp", "reporting_period": "2023-24", "normalised_value": 110.0, "data_status": "FINAL"},
            {"observation_key": "k_zero", "dataset_id": "d1", "indicator_id": "exp", "reporting_period": "2023-24", "normalised_value": 5.0, "data_status": "FINAL"}
        ]
        comp = DataRevisionObservatory.compare_snapshot_versions(
            df_prev=pd.DataFrame(prev_rows),
            df_new=pd.DataFrame(new_rows),
            prev_version_id="v1",
            new_version_id="v2"
        )
        revs = {r["observation_key"]: r for r in comp["revisions"]}

        # Normal revision: 100 -> 110: abs = +10, pct = +10%
        r_norm = revs["k_normal"]
        assert r_norm["absolute_revision"] == 10.0
        assert r_norm["percentage_revision"] == 10.0

        # Zero previous value: 0 -> 5: abs = +5, pct = None (undefined)
        r_zero = revs["k_zero"]
        assert r_zero["absolute_revision"] == 5.0
        assert r_zero["percentage_revision"] is None

    def test_classify_official_source_revision(self):
        """Status change from PROVISIONAL to FINAL is classified as OFFICIAL_SOURCE_REVISION."""
        p_row = {"data_status": "PROVISIONAL_ESTIMATE", "source_release_date": "2024-04-15", "normalised_unit": "USD_B"}
        n_row = {"data_status": "FINAL_RECONCILED", "source_release_date": "2024-10-15", "normalised_unit": "USD_B"}
        cls_type, reason = DataRevisionObservatory._classify_revision(p_row, n_row)
        assert cls_type == RevisionClassification.OFFICIAL_SOURCE_REVISION
        assert "Official status transition" in reason

    def test_classify_pipeline_transformation_correction(self):
        """Pipeline version update with identical source release date is classified as PIPELINE_TRANSFORMATION_CORRECTION."""
        p_row = {"data_status": "FINAL", "source_release_date": "2024-04-15", "normalised_unit": "USD_B"}
        n_row = {"data_status": "FINAL", "source_release_date": "2024-04-15", "normalised_unit": "USD_B"}
        cls_type, reason = DataRevisionObservatory._classify_revision(
            p_row, n_row, pipeline_prev="1.0.0", pipeline_new="2.0.0"
        )
        assert cls_type == RevisionClassification.PIPELINE_TRANSFORMATION_CORRECTION
        assert "Transformation pipeline updated" in reason

    def test_classify_unit_normalization_change(self):
        """Unit change from USD_MILLION to USD_BILLION is classified as UNIT_NORMALIZATION_CHANGE."""
        p_row = {"data_status": "FINAL", "normalised_unit": "USD_MILLION"}
        n_row = {"data_status": "FINAL", "normalised_unit": "USD_BILLION"}
        cls_type, reason = DataRevisionObservatory._classify_revision(p_row, n_row)
        assert cls_type == RevisionClassification.UNIT_NORMALIZATION_CHANGE

    def test_evaluate_revision_alerts_thresholds(self):
        """Emits deduplicated alerts when percentage or absolute revision thresholds are exceeded."""
        revisions = [
            {
                "revision_id": "REV-1",
                "observation_key": "k_huge",
                "dataset_id": "dgcis",
                "indicator_id": "exports",
                "reporting_period": "2023-24",
                "new_version_id": "v2",
                "absolute_revision": 2.50,      # Exceeds default $0.50B
                "percentage_revision": 6.50,     # Exceeds default 3.0%
                "previous_status": "PROVISIONAL",
                "new_status": "FINAL",
                "revision_classification": "OFFICIAL_SOURCE_REVISION"
            }
        ]
        alerts = DataRevisionObservatory.evaluate_revision_alerts(revisions)
        alert_types = [a["alert_type"] for a in alerts]
        assert "LARGE_ABSOLUTE_REVISION" in alert_types
        assert "LARGE_PERCENTAGE_REVISION" in alert_types
        assert "DATA_STATUS_FINALIZED" in alert_types

    def test_calculate_derived_metric_impact(self):
        """Verifies recalculation of trade balance and differences under revised inputs."""
        impacts = DataRevisionObservatory.calculate_derived_metric_impact(
            prev_macro_row={"merchandise_exports_usd_billion": 437.06, "merchandise_imports_usd_billion": 677.24},
            new_macro_row={"merchandise_exports_usd_billion": 437.10, "merchandise_imports_usd_billion": 677.20},
            period_str="FY 2023-24",
            prev_ver_id="v1.0",
            new_ver_id="v1.1"
        )
        tb_impact = [item for item in impacts if item["metric_name"] == "Merchandise Trade Deficit"][0]
        # Prev TB = 437.06 - 677.24 = -240.18
        # New TB = 437.10 - 677.20 = -240.10
        # Absolute diff = -240.10 - (-240.18) = +0.08
        assert tb_impact["previous_value"] == -240.18
        assert tb_impact["new_value"] == -240.10
        assert tb_impact["absolute_diff"] == 0.08

    def test_sqlite_persistence_and_deduplication(self):
        """Persisting identical snapshots repeatedly does not create duplicate entries in data_snapshots."""
        storage = TradeDataStorage()
        snap = ObservationSnapshot(
            snapshot_version_id="test-v-dedup",
            dataset_id="test_ds",
            source_id="SRC_DGCIS",
            observation_key="test_ds:2023:ind",
            indicator_id="ind",
            partner_country=None,
            trade_flow=None,
            reporting_period="2023",
            period_type="CALENDAR_YEAR",
            original_value=50.0,
            normalised_value=50.0,
            original_unit="USD_B",
            normalised_unit="USD_B",
            retrieval_timestamp="2026-10-24T12:00:00Z",
            source_release_date="2024-04-15",
            data_status="FINAL",
            pipeline_version="2.1.0",
            validation_status="VALIDATED"
        ).to_dict()

        # Save twice
        storage.save_data_snapshots([snap])
        storage.save_data_snapshots([snap])

        df_snaps = storage.get_snapshots(snapshot_version_id="test-v-dedup")
        assert len(df_snaps) == 1
