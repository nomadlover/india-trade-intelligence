"""Trade Dependency Analysis Engine for India Trade Intelligence.
Implements Module A: India Trade Dependency Map.
Computes:
1. Supplier / destination partner shares and rankings.
2. Top-1, Top-5, and Top-10 concentration ratios (CR1, CR5, CR10).
3. Herfindahl-Hirschman Index (HHI) with explicit coverage checks and bounds.
4. Multi-year dependency and concentration trajectories.
5. Deterministic, rule-based risk interpretations.
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from india_trade_intelligence.src.analysis.contracts import (
    EconomicDataContract,
    ReportingPeriodType,
    CurrencyUnit
)


class TradeDependencyAnalyzer:
    """Analytical service computing dependency metrics, concentration indices, and structural risk indicators."""

    # Strategic commodity categories and their inherent strategic risk profile
    STRATEGIC_COMMODITIES = {
        "Crude Petroleum": {"criticality": "CRITICAL_ENERGY", "label": "Energy Security & Terms of Trade"},
        "Refined Petroleum Products": {"criticality": "KEY_EXPORT_EARNER", "label": "Refining & Value Addition"},
        "Active Pharmaceutical Ingredients (APIs)": {"criticality": "HEALTH_SECURITY", "label": "Essential Drug Supply Chain"},
        "Pharmaceutical Formulations": {"criticality": "HEALTH_EXPORT", "label": "Global Pharmacy Footprint"},
        "Telecommunications Equipment (Smartphones)": {"criticality": "TECH_MANUFACTURING", "label": "Electronics Assembly & PLI"},
        "Coking Coal & Briquettes": {"criticality": "HEAVY_INDUSTRY", "label": "Blast Furnace Steelmaking Input"},
        "Chemical Fertilisers (Urea/DAP/MOP)": {"criticality": "FOOD_SECURITY", "label": "Agricultural Yield Continuity"},
        "Vegetable Edible Oils (Palm/Soy)": {"criticality": "FOOD_INFLATION", "label": "Dietary Security & Inflation"},
        "Organic & Inorganic Chemicals": {"criticality": "INDUSTRIAL_INPUT", "label": "Downstream Manufacturing Feedstock"},
        "Iron & Steel": {"criticality": "INFRASTRUCTURE", "label": "Capital Goods & Construction"},
        "Industrial Machinery": {"criticality": "CAPITAL_FORMATION", "label": "Productive Capacity Expansion"},
        "Textiles & Ready-made Garments": {"criticality": "EMPLOYMENT_EXPORT", "label": "Labour-Intensive Manufacturing"},
        "Agricultural Cereals (Rice/Wheat)": {"criticality": "AGRI_EXPORTS", "label": "Agricultural Trade & Food Reserve"},
        "Gold & Precious Metals": {"criticality": "NON_ESSENTIAL_CAD", "label": "Current Account Deficit Driver"}
    }

    @staticmethod
    def calculate_hhi_with_coverage(
        shares: List[float],
        expected_total_pct: float = 100.0
    ) -> Dict[str, Any]:
        """Calculates Herfindahl-Hirschman Index (HHI) along with coverage auditing and bounds.
        
        Formula:
            HHI_observed = sum(s_i^2) for each partner share s_i (in percentage points 0-100)
            Scale: 0 to 10,000
            Coverage = sum(s_i)
            Unobserved Share = max(0, 100 - Coverage)
            HHI_max = HHI_observed + (Unobserved Share)^2 (worst-case unobserved concentration)
            
        Thresholds (US DOJ / FTC & International Trade Standards):
            - HHI < 1,500: Unconcentrated / Diversified
            - 1,500 <= HHI < 2,500: Moderately Concentrated
            - HHI >= 2,500: Highly Concentrated
        """
        valid_shares = [float(s) for s in shares if s is not None and not pd.isna(s) and s >= 0]
        
        if not valid_shares:
            return {
                "hhi_observed": 0.0,
                "hhi_max_bound": 0.0,
                "coverage_pct": 0.0,
                "unobserved_pct": 100.0,
                "partner_count": 0,
                "concentration_status": "UNKNOWN",
                "coverage_warning": "No valid partner trade data found."
            }

        coverage_pct = round(sum(valid_shares), 2)
        hhi_observed = round(sum(s ** 2 for s in valid_shares), 2)
        
        # Calculate theoretical unobserved share
        unobserved_pct = max(0.0, round(expected_total_pct - coverage_pct, 2))
        hhi_max_bound = round(hhi_observed + (unobserved_pct ** 2), 2)

        # Classification
        if hhi_observed < 1500:
            status = "DIVERSIFIED"
            status_desc = "Unconcentrated (< 1,500)"
        elif hhi_observed < 2500:
            status = "MODERATE"
            status_desc = "Moderately Concentrated (1,500 - 2,500)"
        else:
            status = "HIGHLY_CONCENTRATED"
            status_desc = "Highly Concentrated (>= 2,500)"

        # Coverage warning threshold: 85%
        coverage_warning = None
        if coverage_pct < 85.0:
            coverage_warning = (
                f"DATA LIMITATION WARNING: Identified partner records account for only {coverage_pct:.1f}% of total trade. "
                f"Observed HHI ({hhi_observed:,.0f}) is an empirical lower bound; worst-case upper bound is {hhi_max_bound:,.0f}."
            )

        return {
            "hhi_observed": hhi_observed,
            "hhi_max_bound": hhi_max_bound,
            "coverage_pct": coverage_pct,
            "unobserved_pct": unobserved_pct,
            "partner_count": len(valid_shares),
            "concentration_status": status,
            "concentration_label": status_desc,
            "coverage_warning": coverage_warning
        }

    @classmethod
    def analyze_dependency(
        cls,
        df_commodity_partner: pd.DataFrame,
        commodity_group: str,
        trade_flow: str,
        financial_year: str
    ) -> Dict[str, Any]:
        """Performs full cross-sectional dependency analysis for a specific commodity and year."""
        # Contract validation: ensure df is valid and not empty
        if df_commodity_partner is None or df_commodity_partner.empty:
            raise ValueError("Bilateral commodity partner dataset is missing or empty.")

        # Normalize trade_flow string (Import / Export)
        flow_clean = "Import" if "imp" in trade_flow.lower() else "Export"

        # Filter dataset
        mask = (
            (df_commodity_partner["commodity_group"] == commodity_group) &
            (df_commodity_partner["trade_flow"] == flow_clean) &
            (df_commodity_partner["financial_year"] == financial_year)
        )
        subset = df_commodity_partner[mask].copy()

        if subset.empty:
            # Check if flow or commodity exists in dataset
            commodities = df_commodity_partner["commodity_group"].unique().tolist()
            years = df_commodity_partner["financial_year"].unique().tolist()
            raise ValueError(
                f"No records found for commodity '{commodity_group}', flow '{flow_clean}', year '{financial_year}'. "
                f"Available commodities: {len(commodities)}, Available years: {len(years)}."
            )

        # Enforce reporting period consistency
        EconomicDataContract.assert_no_mixed_periods(subset["financial_year"])

        # Sort partners by value descending
        subset = subset.sort_values(by="value_usd_million", ascending=False).reset_index(drop=True)

        total_value_usd_m = subset["value_usd_million"].sum()
        total_value_usd_b = round(total_value_usd_m / 1000.0, 3)

        # Partner shares
        shares = subset["partner_share_pct"].tolist()
        partner_names = subset["partner_country"].tolist()
        partner_values = subset["value_usd_million"].tolist()

        # Concentration metrics
        top_1_partner = partner_names[0] if partner_names else "None"
        top_1_share = shares[0] if shares else 0.0
        top_1_val_b = round(partner_values[0] / 1000.0, 3) if partner_values else 0.0

        top_5_share = round(sum(shares[:5]), 2)
        top_10_share = round(sum(shares[:10]), 2)

        # HHI and coverage
        hhi_result = cls.calculate_hhi_with_coverage(shares)

        # Build partner breakdown table
        partner_table = []
        cumulative_share = 0.0
        for i, row in subset.iterrows():
            val_m = row["value_usd_million"]
            val_b = round(val_m / 1000.0, 3)
            share = row["partner_share_pct"]
            cumulative_share = round(cumulative_share + share, 2)
            partner_table.append({
                "rank": i + 1,
                "partner_country": row["partner_country"],
                "value_usd_million": val_m,
                "value_usd_billion": val_b,
                "partner_share_pct": share,
                "cumulative_share_pct": cumulative_share,
                "iso3": row.get("partner_iso3", "OTH")
            })

        partner_df = pd.DataFrame(partner_table)

        # Strategic classification
        strategic_info = cls.STRATEGIC_COMMODITIES.get(
            commodity_group,
            {"criticality": "STANDARD_COMMODITY", "label": "Merchandise Category"}
        )

        result_payload = {
            "commodity_group": commodity_group,
            "trade_flow": flow_clean,
            "financial_year": financial_year,
            "total_value_usd_million": total_value_usd_m,
            "total_value_usd_billion": total_value_usd_b,
            "total_partners_recorded": len(subset),
            "top_1_partner": top_1_partner,
            "top_1_share_pct": top_1_share,
            "top_1_value_usd_billion": top_1_val_b,
            "top_5_share_pct": top_5_share,
            "top_10_share_pct": top_10_share,
            "hhi_score": hhi_result["hhi_observed"],
            "hhi_max_bound": hhi_result["hhi_max_bound"],
            "concentration_status": hhi_result["concentration_status"],
            "concentration_label": hhi_result["concentration_label"],
            "coverage_pct": hhi_result["coverage_pct"],
            "unobserved_pct": hhi_result["unobserved_pct"],
            "coverage_warning": hhi_result["coverage_warning"],
            "strategic_profile": strategic_info,
            "partners_data": partner_df
        }

        # Attach rule-based risk interpretation
        risk_interpretation = cls.generate_rule_based_risk_interpretation(result_payload)
        result_payload["risk_interpretation"] = risk_interpretation

        # Attach research provenance
        provenance = EconomicDataContract.attach_provenance(
            result=result_payload,
            source="Directorate General of Commercial Intelligence and Statistics (DGCI&S)",
            target_period=f"Fiscal Year {financial_year} (April-March)",
            methodology="Herfindahl-Hirschman Index and Concentration Ratios calculated over verified bilateral customs filings.",
            coverage_pct=hhi_result["coverage_pct"]
        )

        return provenance

    @classmethod
    def get_historical_dependency_trends(
        cls,
        df_commodity_partner: pd.DataFrame,
        commodity_group: str,
        trade_flow: str,
        top_n_partners: int = 5
    ) -> pd.DataFrame:
        """Extracts multi-year historical share trajectories for the top N current trading partners."""
        flow_clean = "Import" if "imp" in trade_flow.lower() else "Export"
        mask = (
            (df_commodity_partner["commodity_group"] == commodity_group) &
            (df_commodity_partner["trade_flow"] == flow_clean)
        )
        subset = df_commodity_partner[mask].copy()
        if subset.empty:
            return pd.DataFrame()

        # Identify top N partners in the latest available financial year
        latest_fy = sorted(subset["financial_year"].unique())[-1]
        latest_partners = subset[subset["financial_year"] == latest_fy].sort_values(
            by="value_usd_million", ascending=False
        )["partner_country"].head(top_n_partners).tolist()

        # Filter for these partners across all years
        trend_df = subset[subset["partner_country"].isin(latest_partners)].copy()
        trend_df = trend_df.sort_values(by=["financial_year", "partner_share_pct"], ascending=[True, False])
        return trend_df

    @classmethod
    def get_hhi_trend_series(
        cls,
        df_commodity_partner: pd.DataFrame,
        commodity_group: str,
        trade_flow: str
    ) -> pd.DataFrame:
        """Computes the time series of HHI scores and Top-5 concentration across all available financial years."""
        flow_clean = "Import" if "imp" in trade_flow.lower() else "Export"
        mask = (
            (df_commodity_partner["commodity_group"] == commodity_group) &
            (df_commodity_partner["trade_flow"] == flow_clean)
        )
        subset = df_commodity_partner[mask].copy()
        if subset.empty:
            return pd.DataFrame()

        years = sorted(subset["financial_year"].unique())
        rows = []
        for fy in years:
            fy_data = subset[subset["financial_year"] == fy]
            shares = fy_data["partner_share_pct"].tolist()
            hhi_res = cls.calculate_hhi_with_coverage(shares)
            sorted_shares = sorted(shares, reverse=True)
            cr5 = round(sum(sorted_shares[:5]), 2)
            top1_share = sorted_shares[0] if sorted_shares else 0.0
            top1_partner = fy_data.sort_values(by="value_usd_million", ascending=False).iloc[0]["partner_country"] if not fy_data.empty else "N/A"

            rows.append({
                "financial_year": fy,
                "hhi_observed": hhi_res["hhi_observed"],
                "concentration_status": hhi_res["concentration_status"],
                "coverage_pct": hhi_res["coverage_pct"],
                "cr5_share_pct": cr5,
                "top_1_partner": top1_partner,
                "top_1_share_pct": top1_share,
                "partner_count": len(fy_data)
            })

        return pd.DataFrame(rows)

    @classmethod
    def generate_rule_based_risk_interpretation(cls, result: Dict[str, Any]) -> Dict[str, str]:
        """Generates deterministic, transparent rule-based risk interpretations without subjective speculation.
        Distinguishes:
        - Measured market concentration (HHI & CR)
        - Single-supplier reliance
        - Strategic product criticality
        - Data coverage bounds
        """
        flow = result["trade_flow"]
        commodity = result["commodity_group"]
        top1 = result["top_1_partner"]
        top1_share = result["top_1_share_pct"]
        cr5 = result["top_5_share_pct"]
        hhi = result["hhi_score"]
        status = result["concentration_status"]
        strat = result.get("strategic_profile", {})
        criticality = strat.get("criticality", "STANDARD")
        cov_pct = result["coverage_pct"]

        findings = []

        # 1. Structural Concentration Assessment
        if status == "HIGHLY_CONCENTRATED":
            findings.append(
                f"**High Structural Concentration**: With an HHI of {hhi:,.0f} and the top 5 partners controlling "
                f"{cr5:.1f}% of total {flow.lower()}s, the supply network is concentrated among very few sovereign sources."
            )
        elif status == "MODERATE":
            findings.append(
                f"**Moderate Market Concentration**: With an HHI of {hhi:,.0f} and a 5-partner share of {cr5:.1f}%, "
                f"the market exhibits moderate concentration with intermediate diversification across major bilateral partners."
            )
        else:
            findings.append(
                f"**Broadly Diversified Network**: An HHI of {hhi:,.0f} indicates an unconcentrated, competitive "
                f"bilateral structure across international trading partners."
            )

        # 2. Single-Source Chokepoint Risk
        if top1_share >= 40.0:
            findings.append(
                f"**Single-Source Chokepoint Vulnerability**: **{top1}** commands **{top1_share:.1f}%** of India's total {flow.lower()}s. "
                "Bilateral disruptions, maritime bottlenecks, or geopolitical shifts with this single partner pose acute systemic risk."
            )
        elif top1_share >= 25.0:
            findings.append(
                f"**Prominent Lead Partner Exposure**: **{top1}** is the primary source accounting for **{top1_share:.1f}%** of trade, "
                "representing a material bilateral exposure."
            )
        else:
            findings.append(
                f"**Balanced Lead Share**: Lead partner **{top1}** accounts for **{top1_share:.1f}%**, with no individual nation "
                "exercising monopolistic dominance."
            )

        # 3. Strategic Criticality Interpretation
        if criticality in ("CRITICAL_ENERGY", "HEALTH_SECURITY", "FOOD_SECURITY", "FOOD_INFLATION"):
            findings.append(
                f"**Strategic Economic Necessity**: As a designated **{strat.get('label', 'essential input')}**, supply disruptions "
                "in this category directly transmit into domestic inflation, industrial output shocks, or public health vulnerabilities."
            )
        elif criticality == "KEY_EXPORT_EARNER":
            findings.append(
                f"**Macroeconomic Balance-of-Payments Role**: As a **{strat.get('label', 'key export sector')}**, destination concentration "
                "influences India's hard currency merchandise export realization and current account stability."
            )

        # 4. Coverage caveat
        if cov_pct < 85.0:
            findings.append(
                f"*Data Coverage Note*: The recorded partner entities encompass {cov_pct:.1f}% of customs transactions; "
                "residual unclassified flows may slightly alter effective concentration."
            )

        return {
            "summary_status": status,
            "headline": f"{commodity} ({flow}): {result['concentration_label']} (Lead: {top1} at {top1_share:.1f}%)",
            "detailed_assessment": "\n\n".join(findings)
        }
