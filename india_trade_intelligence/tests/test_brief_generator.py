"""Automated test suite for Module D: Trade Intelligence Brief Generator."""
import pytest
import pandas as pd

from india_trade_intelligence.src.analysis.source_registry import CentralSourceRegistry
from india_trade_intelligence.src.analysis.brief_generator import (
    TradeBriefGenerator,
    EvidencePackage,
    ClaimEvidenceItem
)


class TestTradeBriefGenerator:
    """Verifies evidence package assembly, claim-level provenance, deterministic reporting, and exports."""

    def test_source_registry_metadata(self):
        """Verifies central source registry holds required approved official economic sources."""
        sources = CentralSourceRegistry.list_all_sources()
        source_ids = [s.source_id for s in sources]
        
        assert "SRC_DGCIS" in source_ids
        assert "SRC_RBI_DBIE" in source_ids
        assert "SRC_PPAC" in source_ids
        assert "SRC_MOSPI" in source_ids
        assert "SRC_WORLDBANK_WDI" in source_ids

        dgcis = CentralSourceRegistry.get_source("SRC_DGCIS")
        assert dgcis.publisher == "Ministry of Commerce and Industry, Government of India"
        assert "dgciskol.gov.in" in dgcis.official_url
        assert "Quick estimates" in dgcis.known_limitations

    def test_evidence_package_assembly(self):
        """Assembles deterministic evidence package and verifies core macro metrics."""
        generator = TradeBriefGenerator()
        package = generator.assemble_evidence_package(
            reporting_period="2023-24",
            trade_scope="Aggregate India Trade",
            trade_focus="Import Focus"
        )
        assert package.package_id.startswith("EVP-2023-24")
        assert "EVID_MERCH_EXPORTS" in package.metrics
        assert "EVID_MERCH_IMPORTS" in package.metrics
        assert "EVID_TRADE_BALANCE" in package.metrics
        assert "EVID_SERVICES_EXPORTS" in package.metrics
        assert "EVID_CRUDE_BILL" in package.metrics
        assert "EVID_FX_RATE" in package.metrics

    def test_merchandise_services_separation(self):
        """Guarantees merchandise trade and services trade are strictly separated with distinct sources."""
        generator = TradeBriefGenerator()
        pkg = generator.assemble_evidence_package(reporting_period="2023-24")
        
        merch_exp = pkg.metrics["EVID_MERCH_EXPORTS"]
        serv_exp = pkg.metrics["EVID_SERVICES_EXPORTS"]

        # Distinct source agencies
        assert merch_exp.source_id == "SRC_DGCIS"
        assert serv_exp.source_id == "SRC_RBI_DBIE"

        # Distinct calculation/compilation methodologies
        assert "customs" in merch_exp.calculation_method.lower()
        assert "balance of payments" in serv_exp.calculation_method.lower()

    def test_claim_evidence_linkage(self):
        """Verifies every quantitative claim is traceable to source URL, agency, and calculation method."""
        generator = TradeBriefGenerator()
        pkg = generator.assemble_evidence_package(reporting_period="2023-24")

        for claim_id, item in pkg.metrics.items():
            assert item.claim_id == claim_id
            assert len(item.source_name) > 0
            assert item.source_url.startswith("http")
            assert len(item.calculation_method) > 0
            assert item.data_status in ("FINAL_RECONCILED", "HYPOTHETICAL_SIMULATION", "AUDITED_REVISION")

    def test_report_length_filtering(self):
        """Verifies section filtering for Executive Summary, Standard Brief, and Comprehensive Dossier."""
        generator = TradeBriefGenerator()
        
        # Executive Summary: 4 sections (A, B, I, J)
        pkg_exec = generator.assemble_evidence_package(report_length="Executive Summary")
        assert pkg_exec.supported_sections == ["A", "B", "I", "J"]

        # Standard Brief: 7 sections (A, B, C, D, E, I, J)
        pkg_std = generator.assemble_evidence_package(report_length="Standard Brief")
        assert pkg_std.supported_sections == ["A", "B", "C", "D", "E", "I", "J"]

        # Comprehensive Dossier: 10 sections (A through J)
        pkg_full = generator.assemble_evidence_package(report_length="Comprehensive Intelligence Dossier")
        assert len(pkg_full.supported_sections) == 10

    def test_deterministic_brief_generation_offline(self):
        """Generates full publication-grade brief without external LLM dependencies."""
        generator = TradeBriefGenerator()
        pkg = generator.assemble_evidence_package(
            reporting_period="2023-24",
            trade_scope="Crude Petroleum",
            trade_focus="Import Focus",
            report_length="Comprehensive Intelligence Dossier"
        )
        md = generator.generate_deterministic_brief_markdown(pkg)

        # Check document structure and presence of core sections
        assert "# INDIA TRADE INTELLIGENCE BRIEF" in md
        assert "## A. Executive Summary" in md
        assert "## B. India Trade Overview" in md
        assert "## C. Commodity Composition" in md
        assert "## D. Trading Partner Concentration" in md
        assert "## E. Macroeconomic & Terms-of-Trade Context" in md
        assert "## F. Risk and Supply Chain Dependency Assessment" in md
        assert "## G. Scenario Stress-Testing" in md
        assert "## H. Data Revisions & Provenance Observatory" in md
        assert "## I. Conclusion & Analytical Monitoring Priorities" in md
        assert "## J. Sources, Provenance & Methodological Registry" in md

        # Verify claim ID citations are embedded in text
        assert "[`EVID_MERCH_EXPORTS`]" in md
        assert "[`EVID_MERCH_IMPORTS`]" in md
        assert "[`EVID_TRADE_BALANCE`]" in md

    def test_scenario_shock_labeling(self):
        """Verifies counterfactual scenario outputs are explicitly labeled as hypothetical stress-tests."""
        generator = TradeBriefGenerator()
        pkg = generator.assemble_evidence_package(
            include_scenario=True,
            scenario_preset="Moderate Energy Spike"
        )
        md = generator.generate_deterministic_brief_markdown(pkg)

        assert "NOTICE: The following scenario represents a hypothetical counterfactual simulation" in md
        assert "NOT an official economic forecast" in md

    def test_export_serializers(self):
        """Verifies HTML export and CSV evidence appendix export formats."""
        generator = TradeBriefGenerator()
        pkg = generator.assemble_evidence_package(reporting_period="2023-24")
        md = generator.generate_deterministic_brief_markdown(pkg)

        # HTML Export
        html_out = generator.export_to_html(md, pkg)
        assert "<!DOCTYPE html>" in html_out
        assert "<title>India Trade Intelligence Brief" in html_out
        assert "<table" in html_out
        assert "</html>" in html_out

        # CSV Evidence Appendix Export
        csv_out = generator.export_evidence_appendix_csv(pkg)
        assert "Claim Identifier,Metric Name,Measured Value" in csv_out
        assert "EVID_MERCH_EXPORTS" in csv_out
        assert "SRC_DGCIS" in csv_out
