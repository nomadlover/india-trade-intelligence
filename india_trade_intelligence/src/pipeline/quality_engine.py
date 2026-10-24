"""Provisional Data Quality Status Engine for India Trade Intelligence.
Manages observation-level publication statuses, data quality classifications,
provenance metadata records, and conditional evidence-grounded chart warnings.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

class ObservationPublicationStatus(str, Enum):
    """Reporting and publication status of an economic observation."""
    PRELIMINARY = "PRELIMINARY"
    QUICK_ESTIMATE = "QUICK_ESTIMATE"
    PROVISIONAL = "PROVISIONAL"
    REVISED_PROVISIONAL = "REVISED_PROVISIONAL"
    FINAL_RECONCILED = "FINAL_RECONCILED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN_STATUS = "UNKNOWN_STATUS"

class DataQualityClassification(str, Enum):
    """Rigorous classification of dataset reliability and verification state."""
    VERIFIED_AND_RECONCILED = "VERIFIED_AND_RECONCILED"
    OFFICIAL_BUT_PROVISIONAL = "OFFICIAL_BUT_PROVISIONAL"
    OFFICIAL_ESTIMATE = "OFFICIAL_ESTIMATE"
    SECONDARY_SOURCE_ESTIMATE = "SECONDARY_SOURCE_ESTIMATE"
    POTENTIALLY_AFFECTED_BY_DATA_QUALITY_ISSUE = "POTENTIALLY_AFFECTED_BY_DATA_QUALITY_ISSUE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED = "UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED"

@dataclass
class DataQualityRecord:
    """Comprehensive quality and provenance record for a dataset or observation series."""
    source_name: str
    source_url: str
    observation_period: str
    publication_date: Optional[str]
    retrieval_timestamp: str
    publication_status: ObservationPublicationStatus
    revision_status: str
    reconciliation_status: str
    duplicate_check_status: str
    reporting_period_type: str  # 'CALENDAR_YEAR', 'FINANCIAL_YEAR', 'MONTHLY', 'QUARTERLY'
    estimation_method: str       # 'DIRECT_CUSTOMS_OBSERVATION', 'BOP_SURVEY_COMPILATION', 'EXTRAPOLATION_MODEL', 'BENCHMARK_PROXY'
    known_limitations: List[str] = field(default_factory=list)
    quality_notes: str = ""
    classification: DataQualityClassification = DataQualityClassification.UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "observation_period": self.observation_period,
            "publication_date": self.publication_date,
            "retrieval_timestamp": self.retrieval_timestamp,
            "publication_status": self.publication_status.value,
            "revision_status": self.revision_status,
            "reconciliation_status": self.reconciliation_status,
            "duplicate_check_status": self.duplicate_check_status,
            "reporting_period_type": self.reporting_period_type,
            "estimation_method": self.estimation_method,
            "known_limitations": self.known_limitations,
            "quality_notes": self.quality_notes,
            "classification": self.classification.value
        }

class DataQualityStatusEngine:
    """Evaluates data provenance, propagates status across combined metrics,
    and produces evidence-grounded conditional warnings for the user interface.
    """

    @staticmethod
    def classify_status(
        is_official: bool,
        pub_status: ObservationPublicationStatus,
        is_reconciled: bool,
        has_quality_issue: bool = False,
        is_secondary: bool = False
    ) -> DataQualityClassification:
        """Derives standard data quality classification from verified attributes."""
        if has_quality_issue:
            return DataQualityClassification.POTENTIALLY_AFFECTED_BY_DATA_QUALITY_ISSUE
        if is_secondary:
            return DataQualityClassification.SECONDARY_SOURCE_ESTIMATE
        if not is_official or pub_status == ObservationPublicationStatus.UNKNOWN_STATUS:
            return DataQualityClassification.UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED
        if pub_status == ObservationPublicationStatus.FINAL_RECONCILED and is_reconciled:
            return DataQualityClassification.VERIFIED_AND_RECONCILED
        if pub_status in [ObservationPublicationStatus.PROVISIONAL, ObservationPublicationStatus.QUICK_ESTIMATE, ObservationPublicationStatus.PRELIMINARY]:
            return DataQualityClassification.OFFICIAL_BUT_PROVISIONAL
        if pub_status == ObservationPublicationStatus.ESTIMATED:
            return DataQualityClassification.OFFICIAL_ESTIMATE
        if not is_reconciled:
            return DataQualityClassification.RECONCILIATION_REQUIRED
        return DataQualityClassification.UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED

    @classmethod
    def propagate_combined_status(
        cls,
        merchandise_status: ObservationPublicationStatus,
        services_status: ObservationPublicationStatus
    ) -> Dict[str, Any]:
        """Combines merchandise and services statuses into an audited composite status.
        
        Rule: If any component is PROVISIONAL or ESTIMATED, the combined total must NEVER
        be classified as FINAL_RECONCILED.
        """
        is_provisional = (
            merchandise_status in [ObservationPublicationStatus.PROVISIONAL, ObservationPublicationStatus.QUICK_ESTIMATE, ObservationPublicationStatus.PRELIMINARY] or
            services_status in [ObservationPublicationStatus.PROVISIONAL, ObservationPublicationStatus.QUICK_ESTIMATE, ObservationPublicationStatus.PRELIMINARY]
        )
        is_estimated = (
            merchandise_status == ObservationPublicationStatus.ESTIMATED or
            services_status == ObservationPublicationStatus.ESTIMATED
        )

        if merchandise_status == ObservationPublicationStatus.FINAL_RECONCILED and services_status == ObservationPublicationStatus.FINAL_RECONCILED:
            composite_status = ObservationPublicationStatus.FINAL_RECONCILED
            composite_classification = DataQualityClassification.VERIFIED_AND_RECONCILED
            description = "Both merchandise and services components are officially final and reconciled."
        elif is_provisional and is_estimated:
            composite_status = ObservationPublicationStatus.PROVISIONAL
            composite_classification = DataQualityClassification.OFFICIAL_BUT_PROVISIONAL
            description = "Composite total combines provisional merchandise data with estimated services data. Values are subject to subsequent revision."
        elif is_provisional:
            composite_status = ObservationPublicationStatus.PROVISIONAL
            composite_classification = DataQualityClassification.OFFICIAL_BUT_PROVISIONAL
            description = "Merchandise component is provisional; combined total is subject to revision."
        elif is_estimated:
            composite_status = ObservationPublicationStatus.ESTIMATED
            composite_classification = DataQualityClassification.OFFICIAL_ESTIMATE
            description = "Services component is derived via preliminary statistical estimation."
        else:
            composite_status = ObservationPublicationStatus.UNKNOWN_STATUS
            composite_classification = DataQualityClassification.UNKNOWN_OR_INSUFFICIENTLY_DOCUMENTED
            description = "One or more component statuses are unverified."

        return {
            "composite_status": composite_status,
            "composite_classification": composite_classification,
            "description": description,
            "merchandise_status": merchandise_status,
            "services_status": services_status,
            "is_final": (composite_status == ObservationPublicationStatus.FINAL_RECONCILED)
        }

    @staticmethod
    def generate_chart_warning(
        warning_type: str,
        custom_details: Optional[str] = None
    ) -> Optional[str]:
        """Generates evidence-grounded conditional warnings based on standard templates.
        
        Supported warning_types:
          - 'PROVISIONAL_MERCHANDISE' (Example A)
          - 'ESTIMATED_SERVICES' (Example B)
          - 'UNRECONCILED_DUPLICATION_RISK' (Example C)
          - 'COMBINED_TOTALS' (Example D)
          - 'PARTIAL_YEAR' (Example E)
          - 'SEZ_ICEGATE_CONDITIONAL'
        """
        templates = {
            "PROVISIONAL_MERCHANDISE": (
                "Reporting status: Provisional. Values may be revised in subsequent releases."
            ),
            "ESTIMATED_SERVICES": (
                "Reporting status: Estimated. See the source methodology for the estimation approach."
            ),
            "UNRECONCILED_DUPLICATION_RISK": (
                "Data quality warning: This dataset has not yet been reconciled against the applicable official reference totals. "
                "Potential duplication or reporting inconsistencies may affect interpretation."
            ),
            "COMBINED_TOTALS": (
                "Data note: This total combines merchandise and services components with different source methodologies or reporting statuses. "
                "See component-level details."
            ),
            "PARTIAL_YEAR": (
                "Coverage: Partial reporting year. Do not compare this total directly with a complete annual total without adjusting for the reporting period."
            ),
            "SEZ_ICEGATE_CONDITIONAL": (
                "Data quality notice: This dataset is provisional or undergoing reconciliation. "
                "Potential duplication or reporting inconsistencies have been identified or cannot yet be ruled out. "
                "Interpret affected comparisons cautiously. See source notes for details."
            )
        }

        base = templates.get(warning_type)
        if not base:
            return None
        if custom_details:
            return f"{base} Details: {custom_details}"
        return base
