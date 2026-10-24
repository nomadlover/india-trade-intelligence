"""Central Source Registry for India Trade Intelligence.
Maintains auditable, authoritative metadata for all approved official economic data providers.
Enforces empirical grounding and explicit limitation disclosure across briefs and observatory.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


@dataclass
class OfficialSourceDefinition:
    """Standardized metadata definition for an approved economic data provider."""
    source_id: str
    source_name: str
    publisher: str
    official_url: str
    dataset_or_indicator: str
    geographic_coverage: str
    reporting_frequency: str
    standard_units: str
    historical_coverage: str
    known_limitations: str
    retrieval_method: str
    last_verified_date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CentralSourceRegistry:
    """Official repository of authorized economic sources."""

    _SOURCES: Dict[str, OfficialSourceDefinition] = {
        "SRC_DGCIS": OfficialSourceDefinition(
            source_id="SRC_DGCIS",
            source_name="Directorate General of Commercial Intelligence and Statistics (DGCI&S)",
            publisher="Ministry of Commerce and Industry, Government of India",
            official_url="https://dgciskol.gov.in",
            dataset_or_indicator="Merchandise Trade Statistics — Bilateral Partner & Principal Commodity 8-digit ITC-HS",
            geographic_coverage="India National & Bilateral Sovereign Trade",
            reporting_frequency="Monthly Quick Estimates, Monthly Provisional, Annual Financial Year (April–March)",
            standard_units="USD Million and INR Crore",
            historical_coverage="FY 2013-14 through FY 2023-24 (Final); FY 2024-25 Q1 & FY 2025-26 (Provisional/Interim)",
            known_limitations=(
                "Quick estimates released within 15 days of month-end are subject to subsequent customs reconciliation "
                "via ICEGATE EDI. Provisional figures undergo retrospective adjustments as supplementary shipping bills "
                "and SEZ transactions are finalized."
            ),
            retrieval_method="Official Customs EDI Portal / Published Statistical Bulletins",
            last_verified_date="2026-03-31"
        ),
        "SRC_RBI_DBIE": OfficialSourceDefinition(
            source_id="SRC_RBI_DBIE",
            source_name="Reserve Bank of India — Database on Indian Economy (DBIE)",
            publisher="Reserve Bank of India",
            official_url="https://dbie.rbi.org.in",
            dataset_or_indicator="Balance of Payments (BPM6), Services Trade, External Debt, Foreign Exchange Reserves, INR Exchange Rates & REER",
            geographic_coverage="India National Macroeconomic & External Sector",
            reporting_frequency="Daily/Monthly (FX Reserves, Exchange Rates), Quarterly (Balance of Payments, CAD)",
            standard_units="USD Billion, INR Crore, Exchange Rate (INR per USD)",
            historical_coverage="1995 through 2025 (Annual / Quarterly / Monthly)",
            known_limitations=(
                "Monthly services trade releases are preliminary estimates derived from banking transaction records "
                "(FETERS), finalized upon quarterly comprehensive Balance of Payments publication."
            ),
            retrieval_method="RBI DBIE Structured API / Statistical Releases",
            last_verified_date="2026-03-31"
        ),
        "SRC_PPAC": OfficialSourceDefinition(
            source_id="SRC_PPAC",
            source_name="Petroleum Planning & Analysis Cell (PPAC)",
            publisher="Ministry of Petroleum and Natural Gas, Government of India",
            official_url="https://www.ppac.gov.in",
            dataset_or_indicator="Indian Basket Crude Oil Prices, Petroleum Import/Export Volumes & Values, Refinery Production",
            geographic_coverage="India Energy Sector & Global Hydrocarbon Benchmarks",
            reporting_frequency="Daily Price Tracking, Monthly Hydrocarbon Data",
            standard_units="USD per barrel ($/bbl), Million Metric Tonnes (MMT), USD Billion",
            historical_coverage="2010 through 2025 (Monthly & Annual)",
            known_limitations=(
                "Indian basket crude price is a weighted composite benchmark (Oman & Dubai sour crude vs Brent sweet crude). "
                "Refinery import costs may deviate slightly based on bilateral term contracts, Russian Urals discounts, and freight spreads."
            ),
            retrieval_method="PPAC Monthly Hydrocarbon Bulletins & Daily Published Benchmarks",
            last_verified_date="2026-03-31"
        ),
        "SRC_MOSPI": OfficialSourceDefinition(
            source_id="SRC_MOSPI",
            source_name="Ministry of Statistics and Programme Implementation (MoSPI)",
            publisher="Central Statistics Office (CSO) / MoSPI, Government of India",
            official_url="https://mospi.gov.in",
            dataset_or_indicator="Consumer Price Index (CPI Headline 2012=100), Index of Industrial Production (IIP), Nominal and Real GDP",
            geographic_coverage="India National (Urban + Rural Combined)",
            reporting_frequency="Monthly (CPI, IIP), Quarterly and Annual (National Accounts / GDP)",
            standard_units="Index Level, YoY Percentage Change (%), INR Lakh Crore",
            historical_coverage="2011 through 2025 (Monthly CPI Series)",
            known_limitations=(
                "Base year revision updates may create structural level shifts. Provisional CPI prints are released on the "
                "12th of each month and finalized in the subsequent release."
            ),
            retrieval_method="MoSPI Official Press Releases & Statistical Datasets",
            last_verified_date="2026-03-31"
        ),
        "SRC_WORLDBANK_WDI": OfficialSourceDefinition(
            source_id="SRC_WORLDBANK_WDI",
            source_name="World Bank — World Development Indicators (WDI)",
            publisher="International Bank for Reconstruction and Development / The World Bank",
            official_url="https://databank.worldbank.org/source/world-development-indicators",
            dataset_or_indicator="Long-Run Annual Trade Openness, Exports/Imports GNFS, GDP at Current USD, Inflation Deflator",
            geographic_coverage="India (Sovereign) and International Comparators",
            reporting_frequency="Annual (Calendar Year basis: January 1 to December 31)",
            standard_units="Nominal Current USD, Percentage of GDP (%)",
            historical_coverage="1960 through 2024 (Verified Annual Series)",
            known_limitations=(
                "Reports on Calendar Year (CY) basis, distinct from Indian Financial Year (FY April-March). "
                "Observations cannot be directly substituted for Indian fiscal year customs filings."
            ),
            retrieval_method="World Bank Data API v2 (JSON REST endpoint)",
            last_verified_date="2026-03-31"
        ),
        "SRC_DOC_TRADESTAT": OfficialSourceDefinition(
            source_id="SRC_DOC_TRADESTAT",
            source_name="Department of Commerce — TradeStat System",
            publisher="Ministry of Commerce and Industry, Government of India",
            official_url="https://tradestat.commerce.gov.in",
            dataset_or_indicator="Principal Commodity Classifications, Export Promotion Council Aggregations, Trade Policy Targets",
            geographic_coverage="India Foreign Trade & Free Trade Agreement Partners",
            reporting_frequency="Monthly & Fiscal Year Aggregations",
            standard_units="USD Million and INR Crore",
            historical_coverage="FY 2013-14 through FY 2024-25 Q1",
            known_limitations=(
                "Categorizes commodities by 168 principal commodity groupings, slightly broader than disaggregated 8-digit HS customs codes."
            ),
            retrieval_method="Department of Commerce Portal Export Tables",
            last_verified_date="2026-03-31"
        )
    }

    @classmethod
    def get_source(cls, source_id: str) -> Optional[OfficialSourceDefinition]:
        """Retrieves official source definition by unique identifier."""
        return cls._SOURCES.get(source_id)

    @classmethod
    def list_all_sources(cls) -> List[OfficialSourceDefinition]:
        """Returns list of all authorized official sources."""
        return list(cls._SOURCES.values())

    @classmethod
    def resolve_source_by_dataset(cls, dataset_id: str) -> OfficialSourceDefinition:
        """Maps dataset or table identifier to its authoritative official source."""
        mapping = {
            "dgcis_bilateral": "SRC_DGCIS",
            "bilateral_trade": "SRC_DGCIS",
            "commodity_trade": "SRC_DGCIS",
            "dgcis_commodities": "SRC_DGCIS",
            "commodity_partner_trade": "SRC_DGCIS",
            "monthly_trade": "SRC_RBI_DBIE",
            "rbi_monthly": "SRC_RBI_DBIE",
            "external_sector_macro": "SRC_RBI_DBIE",
            "trading_partner_conditions": "SRC_RBI_DBIE",
            "energy_commodity_exposure": "SRC_PPAC",
            "macro_annual": "SRC_WORLDBANK_WDI",
            "world_bank_macro": "SRC_WORLDBANK_WDI",
            "cpi_inflation": "SRC_MOSPI",
            "trade_policy_events": "SRC_DOC_TRADESTAT"
        }
        src_id = mapping.get(dataset_id.lower(), "SRC_DGCIS")
        return cls._SOURCES[src_id]
