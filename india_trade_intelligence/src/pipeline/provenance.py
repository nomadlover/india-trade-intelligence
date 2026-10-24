"""Data Provenance and Metadata Architecture for India Trade Intelligence.
Provides research-grade metadata standards covering metric identity, official source,
observation period, frequency, accounting definitions, formulas, and data status.
Every major KPI and visualization is grounded in this provenance structure.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

@dataclass(frozen=True)
class MetricProvenance:
    """Rigorous metadata record for an economic indicator or trade dataset."""
    metric_id: str
    name: str
    source: str
    source_agency: str
    observation_period: str
    frequency: str
    unit: str
    definition: str
    calculation: str
    data_status: str  # "Official Final", "Provisional / Interim", "Derived Identity", "Benchmark Proxy"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary_badge_text(self) -> str:
        return f"{self.data_status} | {self.observation_period} | {self.source_agency} | Unit: {self.unit}"


# Canonical Provenance Registry
PROVENANCE_REGISTRY: Dict[str, MetricProvenance] = {
    "macro_exports_gnfs": MetricProvenance(
        metric_id="macro_exports_gnfs",
        name="Total Exports of Goods and Services",
        source="World Bank World Development Indicators (WDI)",
        source_agency="World Bank Group [Series: NE.EXP.GNFS.CD]",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (CY: January - December)",
        unit="Current US$ Billion",
        definition=(
            "Value of all goods and market services provided to the rest of the world, "
            "including merchandise, freight, insurance, travel, telecommunications, "
            "and business services on a Balance of Payments (BoP) basis."
        ),
        calculation="Sum of recorded BoP credit entries for goods and services converted to US dollars at official annual exchange rates.",
        data_status="Official Final (1995–2024)",
        notes="Basis: Balance of Payments (BoP). Includes both physical goods and intangible services (e.g. IT, consulting)."
    ),
    "macro_imports_gnfs": MetricProvenance(
        metric_id="macro_imports_gnfs",
        name="Total Imports of Goods and Services",
        source="World Bank World Development Indicators (WDI)",
        source_agency="World Bank Group [Series: NE.IMP.GNFS.CD]",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (CY: January - December)",
        unit="Current US$ Billion",
        definition=(
            "Value of all goods and market services received from the rest of the world "
            "on a Balance of Payments (BoP) basis."
        ),
        calculation="Sum of recorded BoP debit entries for goods and services converted to US dollars.",
        data_status="Official Final (1995–2024)",
        notes="Basis: Balance of Payments (BoP). Captures gross goods and services purchases from abroad."
    ),
    "macro_trade_balance": MetricProvenance(
        metric_id="macro_trade_balance",
        name="Net Trade Balance (Goods & Services)",
        source="Derived from World Bank WDI",
        source_agency="Computed from World Bank Series NE.EXP.GNFS.CD and NE.IMP.GNFS.CD",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (CY)",
        unit="Current US$ Billion",
        definition="The net balance of goods and services trade; difference between total exports and total imports.",
        calculation="Accounting Identity: Trade Balance = Exports - Imports",
        data_status="Derived Accounting Identity",
        notes="A negative figure indicates a trade deficit; positive indicates a surplus. BoP basis."
    ),
    "macro_trade_openness": MetricProvenance(
        metric_id="macro_trade_openness",
        name="Trade Openness Ratio (% of GDP)",
        source="Derived from World Bank WDI",
        source_agency="Computed from World Bank Series NE.EXP.GNFS.CD, NE.IMP.GNFS.CD, NY.GDP.MKTP.CD",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (CY)",
        unit="Percentage of GDP (%)",
        definition="The degree of global economic integration measured by total trade volume relative to domestic output.",
        calculation="Formula: ((Exports + Imports) / GDP) * 100",
        data_status="Derived Econometric Metric",
        notes="Expressed as % of nominal GDP in current US dollars."
    ),
    "macro_gdp": MetricProvenance(
        metric_id="macro_gdp",
        name="Gross Domestic Product (Nominal)",
        source="World Bank World Development Indicators (WDI)",
        source_agency="World Bank Group [Series: NY.GDP.MKTP.CD]",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (CY)",
        unit="Current US$ Billion",
        definition="Gross value added by all resident producers in the economy plus product taxes minus subsidies.",
        calculation="National accounts aggregate compiled at market prices and converted to current US dollars.",
        data_status="Official Final (1995–2024)",
        notes="Nominal figures in current US dollars; not adjusted for inflation."
    ),
    "macro_exchange_rate": MetricProvenance(
        metric_id="macro_exchange_rate",
        name="Official Exchange Rate (INR per USD)",
        source="World Bank WDI / Reserve Bank of India",
        source_agency="World Bank Group [Series: PA.NUS.FCRF] & RBI Reference Rates",
        observation_period="1995–2024 (Annual)",
        frequency="Calendar Year (Annual Period Average)",
        unit="Indian Rupee (INR) per US Dollar (USD)",
        definition="Official exchange rate determined by national authorities in legally sanctioned foreign exchange markets.",
        calculation="Arithmetic mean of daily official interbank foreign exchange market reference rates.",
        data_status="Official Final",
        notes="Period average, not end-of-period rate."
    ),
    "macro_cpi_inflation": MetricProvenance(
        metric_id="macro_cpi_inflation",
        name="Consumer Price Index (CPI) Inflation Rate",
        source="World Bank WDI / MoSPI",
        source_agency="World Bank Group [Series: FP.CPI.TOTL.ZG] & MoSPI National Accounts",
        observation_period="1995–2024 (30 Annual Observations)",
        frequency="Calendar Year (Annual % Change)",
        unit="Percentage Change per Annum (%)",
        definition="Annual percentage change in the cost to the average consumer of acquiring a basket of goods and services.",
        calculation="Formula: ((CPI_t - CPI_{t-1}) / CPI_{t-1}) * 100",
        data_status="Official Final (30 Observations: 1995–2024)",
        notes="All-India headline CPI inflation. Long-run sample mean is 5.82% annually over 1995–2024."
    ),
    "bilateral_merchandise_trade": MetricProvenance(
        metric_id="bilateral_merchandise_trade",
        name="Bilateral Merchandise Trade by Partner Nation",
        source="Directorate General of Commercial Intelligence and Statistics (DGCI&S)",
        source_agency="Department of Commerce, Ministry of Commerce and Industry, Government of India",
        observation_period="FY 2013-14 to FY 2023-24 (Final); FY 2024-25 Q1 (Provisional)",
        frequency="Financial Year (FY: April 1 - March 31)",
        unit="US$ Million & INR Crore",
        definition="Cross-border physical merchandise movements cleared through Indian customs ports of entry and exit.",
        calculation="Aggregation of individual customs import bills of entry (CIF valuation) and export shipping bills (FOB valuation).",
        data_status="Official Final (FY14–FY24); Provisional Q1 (FY25)",
        notes="Customs basis. Excludes services trade (software, remittances, travel) and informal border barter."
    ),
    "commodity_merchandise_trade": MetricProvenance(
        metric_id="commodity_merchandise_trade",
        name="Principal Commodity Group Trade Composition",
        source="Directorate General of Commercial Intelligence and Statistics (DGCI&S)",
        source_agency="Department of Commerce, Ministry of Commerce and Industry, Government of India",
        observation_period="FY 2013-14 to FY 2023-24 (Final); FY 2024-25 Q1 (Provisional)",
        frequency="Financial Year (FY: April 1 - March 31)",
        unit="US$ Million & INR Crore",
        definition="Merchandise exports and imports classified into 17 standard principal commodity sectors based on ITC-HS.",
        calculation="Sum of harmonized tariff code items mapped into principal sectoral chapters.",
        data_status="Official Final (FY14–FY24); Provisional Q1 (FY25)",
        notes="Covers merchandise trade only. Principal groups include Petroleum Products, Electronic Goods, Engineering Goods, etc."
    ),
    "monthly_merchandise_trade": MetricProvenance(
        metric_id="monthly_merchandise_trade",
        name="High-Frequency Monthly Merchandise Trade",
        source="Reserve Bank of India (DBIE) / Ministry of Commerce",
        source_agency="RBI Database on Indian Economy & DGCI&S Press Releases",
        observation_period="2018-01 to 2025-03 (Monthly)",
        frequency="Monthly (Calendar Month)",
        unit="US$ Million",
        definition="Monthly customs merchandise trade aggregates tracking gross exports, gross imports, oil imports, and non-oil balances.",
        calculation="Monthly customs compilation by DGCI&S, published in RBI Monthly Bulletin.",
        data_status="Official Monthly Series",
        notes="Customs basis. Non-oil balances isolate core industrial trade from volatile hydrocarbon swings."
    ),
    "commodity_basket_benchmark": MetricProvenance(
        metric_id="commodity_basket_benchmark",
        name="Representative Historical Retail Commodity Price Benchmarks",
        source="Documented Indian Retail Market Price Benchmarks",
        source_agency="Public retail market records, PSU fuel tariffs, and consumer bullion associations",
        observation_period="Milestone Years: 1995, 2000, 2005, 2010, 2015, 2020, 2024, 2025",
        frequency="Decadal & Quinquennial Milestones",
        unit="INR (₹) per physical unit",
        definition=(
            "Representative price proxies for tangible consumer and energy goods "
            "(staple food, transport fuel, domestic LPG, cinema ticket, wholesome meal, gold) "
            "used to simulate physical purchasing power changes across eras."
        ),
        calculation="Affordable Quantity = Nominal Amount / Benchmark Retail Price",
        data_status="Benchmark Proxy (Not Official Headline CPI)",
        notes=(
            "Representative historical retail benchmarks documented for consumer purchasing-power simulation; "
            "these series are illustrative physical proxies and are NOT the official MoSPI headline CPI index."
        )
    )
}

def get_provenance(metric_id: str) -> Optional[MetricProvenance]:
    """Retrieves metadata provenance record for a given metric identifier."""
    return PROVENANCE_REGISTRY.get(metric_id)

def get_all_provenance() -> Dict[str, MetricProvenance]:
    """Returns the full dictionary of provenance records."""
    return PROVENANCE_REGISTRY

def render_data_status_badge(metric_id: str = "macro_exports_gnfs") -> str:
    """Renders a standardized HTML status badge for the UI."""
    prov = PROVENANCE_REGISTRY.get(metric_id)
    if not prov:
        return ""
    
    return f"""
    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; margin: 8px 0; font-size: 0.80rem; color: #cbd5e1; display: inline-flex; align-items: center; gap: 8px;">
        <span style="background-color: #0369a1; color: #f0f9ff; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.72rem;">{prov.data_status}</span>
        <span><strong>Period:</strong> {prov.observation_period}</span>
        <span style="color: #64748b;">|</span>
        <span><strong>Source:</strong> {prov.source}</span>
        <span style="color: #64748b;">|</span>
        <span><strong>Unit:</strong> {prov.unit}</span>
    </div>
    """
