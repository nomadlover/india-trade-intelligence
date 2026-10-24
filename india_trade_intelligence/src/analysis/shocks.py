"""Trade Shock Simulation Engine for India Trade Intelligence.
Implements Module B: Trade Shock Simulator.
Models:
1. Crude oil price shocks (mechanical accounting and short-run price elasticity).
2. INR/USD exchange rate shocks (depreciation/appreciation pass-through and valuation).
3. Global export demand shocks.
4. Combined multi-factor shock engine with strict order-of-operations.
5. 2D Sensitivity analysis matrix (Crude Oil vs INR/USD).
6. Scenario comparison presets and serialization (JSON/CSV).
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import pandas as pd
import numpy as np

from india_trade_intelligence.src.analysis.contracts import (
    EconomicDataContract,
    ReportingPeriodType,
    CurrencyUnit
)


@dataclass
class ShockBaseline:
    """Empirical baseline macroeconomic and trade parameters for simulation."""
    period_label: str
    crude_price_usd_per_bbl: float
    crude_volume_mmt: float
    crude_import_bill_usd_b: float
    non_oil_imports_usd_b: float
    total_imports_usd_b: float
    total_exports_usd_b: float
    trade_balance_usd_b: float
    exchange_rate_inr_per_usd: float
    trade_balance_inr_crore: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TradeShockSimulator:
    """Simulation engine for macroeconomic trade shocks with empirical grounding."""

    # Standard empirical benchmarks
    BARRELS_PER_METRIC_TON = 7.33  # PPAC standard crude conversion factor
    DEFAULT_CRUDE_PRICE = 84.50     # USD per barrel (FY24 average)
    DEFAULT_CRUDE_VOLUME_MMT = 232.5 # Million Metric Tonnes (FY24)
    DEFAULT_EXCHANGE_RATE = 83.50   # INR per USD (FY24 average)
    DEFAULT_EXPORTS_USD_B = 437.1   # Merchandise exports USD Billion (FY24)
    DEFAULT_IMPORTS_USD_B = 677.2   # Merchandise imports USD Billion (FY24)

    # Standard presets
    PRESETS = {
        "Baseline (Zero Shock)": {
            "description": "Unperturbed empirical baseline conditions (0% shocks across all dimensions).",
            "oil_price_shock_pct": 0.0,
            "fx_depreciation_pct": 0.0,
            "export_demand_shock_pct": 0.0,
            "crude_demand_elasticity": 0.0
        },
        "Moderate Energy Spike": {
            "description": "Geopolitical friction elevating crude prices by +15% with mild 3% rupee depreciation.",
            "oil_price_shock_pct": 15.0,
            "fx_depreciation_pct": 3.0,
            "export_demand_shock_pct": -2.0,
            "crude_demand_elasticity": -0.05
        },
        "Severe Stagflation Crisis": {
            "description": "Stagflationary global supply shock (+40% crude oil, 10% INR depreciation, -8% global export contraction).",
            "oil_price_shock_pct": 40.0,
            "fx_depreciation_pct": 10.0,
            "export_demand_shock_pct": -8.0,
            "crude_demand_elasticity": -0.10
        },
        "Global Disinflation Windfall": {
            "description": "Global supply recovery (-20% crude oil, 2% rupee appreciation, +5% global export expansion).",
            "oil_price_shock_pct": -20.0,
            "fx_depreciation_pct": -2.0,
            "export_demand_shock_pct": 5.0,
            "crude_demand_elasticity": -0.05
        }
    }

    @classmethod
    def get_empirical_baseline(
        cls,
        df_energy: Optional[pd.DataFrame] = None,
        df_macro: Optional[pd.DataFrame] = None,
        df_ext: Optional[pd.DataFrame] = None
    ) -> ShockBaseline:
        """Extracts empirical baseline parameters from loaded dataframes or applies verified defaults."""
        # 1. Crude oil & energy parameters
        crude_price = cls.DEFAULT_CRUDE_PRICE
        crude_vol = cls.DEFAULT_CRUDE_VOLUME_MMT
        crude_bill = round((crude_vol * 1e6 * cls.BARRELS_PER_METRIC_TON * crude_price) / 1e9, 2)
        
        if df_energy is not None and not df_energy.empty:
            latest_e = df_energy.iloc[-1]
            if "indian_basket_crude_usd_per_bbl" in latest_e and pd.notna(latest_e["indian_basket_crude_usd_per_bbl"]):
                crude_price = float(latest_e["indian_basket_crude_usd_per_bbl"])
            elif "indian_basket_crude_usd_bbl" in latest_e and pd.notna(latest_e["indian_basket_crude_usd_bbl"]):
                crude_price = float(latest_e["indian_basket_crude_usd_bbl"])
                
            if "crude_import_quantity_mmt" in latest_e and pd.notna(latest_e["crude_import_quantity_mmt"]):
                crude_vol = float(latest_e["crude_import_quantity_mmt"])
            elif "crude_oil_import_volume_mmt" in latest_e and pd.notna(latest_e["crude_oil_import_volume_mmt"]):
                crude_vol = float(latest_e["crude_oil_import_volume_mmt"])
                
            if "crude_import_bill_usd_billion" in latest_e and pd.notna(latest_e["crude_import_bill_usd_billion"]):
                crude_bill = float(latest_e["crude_import_bill_usd_billion"])

        # 2. Macro exports, imports, and exchange rate
        exports_usd_b = cls.DEFAULT_EXPORTS_USD_B
        imports_usd_b = cls.DEFAULT_IMPORTS_USD_B
        fx_rate = cls.DEFAULT_EXCHANGE_RATE
        
        if df_macro is not None and not df_macro.empty:
            latest_m = df_macro.iloc[-1]
            if "merchandise_exports_usd_billion" in latest_m and pd.notna(latest_m["merchandise_exports_usd_billion"]):
                exports_usd_b = float(latest_m["merchandise_exports_usd_billion"])
            if "merchandise_imports_usd_billion" in latest_m and pd.notna(latest_m["merchandise_imports_usd_billion"]):
                imports_usd_b = float(latest_m["merchandise_imports_usd_billion"])
            if "exchange_rate_inr_per_usd" in latest_m and pd.notna(latest_m["exchange_rate_inr_per_usd"]):
                fx_rate = float(latest_m["exchange_rate_inr_per_usd"])

        if df_ext is not None and not df_ext.empty:
            latest_x = df_ext.iloc[-1]
            if "inr_per_usd_exchange_rate" in latest_x and pd.notna(latest_x["inr_per_usd_exchange_rate"]):
                fx_rate = float(latest_x["inr_per_usd_exchange_rate"])

        # Derived baseline accounting identities
        non_oil_imports_usd_b = round(max(0.0, imports_usd_b - crude_bill), 2)
        trade_balance_usd_b = round(exports_usd_b - imports_usd_b, 2)
        trade_balance_inr_crore = round(EconomicDataContract.to_inr_crore(trade_balance_usd_b, fx_rate), 2)

        return ShockBaseline(
            period_label="FY 2024-25 Empirical Baseline",
            crude_price_usd_per_bbl=round(crude_price, 2),
            crude_volume_mmt=round(crude_vol, 2),
            crude_import_bill_usd_b=round(crude_bill, 2),
            non_oil_imports_usd_b=non_oil_imports_usd_b,
            total_imports_usd_b=round(imports_usd_b, 2),
            total_exports_usd_b=round(exports_usd_b, 2),
            trade_balance_usd_b=trade_balance_usd_b,
            exchange_rate_inr_per_usd=round(fx_rate, 2),
            trade_balance_inr_crore=trade_balance_inr_crore
        )

    @classmethod
    def simulate_crude_oil_shock(
        cls,
        baseline: ShockBaseline,
        price_shock_pct: float,
        elasticity_vol: float = 0.0
    ) -> Dict[str, Any]:
        """Simulates crude oil import bill response under price shock with optional volume elasticity.
        
        Accounting:
            P_scenario = P_baseline * (1 + shock / 100)
            V_scenario = V_baseline * (1 + elasticity * shock / 100) (constrained >= 0)
            Bill_scenario = (V_scenario in bbl * P_scenario) / 10^9
            Delta Bill = Bill_scenario - Bill_baseline
        """
        p0 = baseline.crude_price_usd_per_bbl
        v0_mmt = baseline.crude_volume_mmt
        bill0 = baseline.crude_import_bill_usd_b

        # Identity guard for zero shock
        if price_shock_pct == 0.0 and elasticity_vol == 0.0:
            return {
                "baseline_price_usd_per_bbl": p0,
                "price_shock_pct": 0.0,
                "scenario_price_usd_per_bbl": p0,
                "baseline_volume_mmt": v0_mmt,
                "elasticity_volume": elasticity_vol,
                "scenario_volume_mmt": v0_mmt,
                "baseline_oil_bill_usd_b": bill0,
                "scenario_oil_bill_usd_b": bill0,
                "delta_oil_bill_usd_b": 0.0,
                "delta_oil_bill_pct": 0.0,
                "delta_oil_bill_inr_crore": 0.0
            }

        p1 = round(p0 * (1.0 + price_shock_pct / 100.0), 2)
        
        # Volume response if elasticity specified (e.g. -0.1 means 10% price rise reduces volume by 1%)
        vol_change_factor = 1.0 + (elasticity_vol * price_shock_pct / 100.0)
        vol_change_factor = max(0.2, vol_change_factor)  # Floor at 80% contraction for extreme stability
        v1_mmt = round(v0_mmt * vol_change_factor, 2)

        # Recompute expenditure in USD Billion
        # Standard: 1 MMT = 10^6 MT = 7.33 * 10^6 barrels
        total_bbl = v1_mmt * 1e6 * cls.BARRELS_PER_METRIC_TON
        bill1 = round((total_bbl * p1) / 1e9, 2)

        delta_bill_usd_b = round(bill1 - bill0, 2)
        delta_bill_pct = round((delta_bill_usd_b / bill0 * 100.0), 2) if bill0 > 0 else 0.0
        delta_bill_inr_crore = round(EconomicDataContract.to_inr_crore(delta_bill_usd_b, baseline.exchange_rate_inr_per_usd), 2)

        return {
            "baseline_price_usd_per_bbl": p0,
            "price_shock_pct": price_shock_pct,
            "scenario_price_usd_per_bbl": p1,
            "baseline_volume_mmt": v0_mmt,
            "elasticity_volume": elasticity_vol,
            "scenario_volume_mmt": v1_mmt,
            "baseline_oil_bill_usd_b": bill0,
            "scenario_oil_bill_usd_b": bill1,
            "delta_oil_bill_usd_b": delta_bill_usd_b,
            "delta_oil_bill_pct": delta_bill_pct,
            "delta_oil_bill_inr_crore": delta_bill_inr_crore
        }

    @classmethod
    def simulate_exchange_rate_shock(
        cls,
        baseline: ShockBaseline,
        depreciation_pct: float
    ) -> Dict[str, Any]:
        """Simulates INR/USD exchange rate shock and its nominal Rupee valuation effects.
        
        Convention:
            Positive (+) depreciation_pct = INR depreciates (more INR per USD).
            Negative (-) depreciation_pct = INR appreciates (fewer INR per USD).
            e_scenario = e_baseline * (1 + depr / 100)
        """
        e0 = baseline.exchange_rate_inr_per_usd
        e1 = round(e0 * (1.0 + depreciation_pct / 100.0), 4)

        # Baseline in INR Crore
        exp_inr0 = round(EconomicDataContract.to_inr_crore(baseline.total_exports_usd_b, e0), 2)
        imp_inr0 = round(EconomicDataContract.to_inr_crore(baseline.total_imports_usd_b, e0), 2)
        bal_inr0 = round(EconomicDataContract.to_inr_crore(baseline.trade_balance_usd_b, e0), 2)

        # Scenario in INR Crore (mechanical valuation at new exchange rate)
        exp_inr1 = round(EconomicDataContract.to_inr_crore(baseline.total_exports_usd_b, e1), 2)
        imp_inr1 = round(EconomicDataContract.to_inr_crore(baseline.total_imports_usd_b, e1), 2)
        bal_inr1 = round(EconomicDataContract.to_inr_crore(baseline.trade_balance_usd_b, e1), 2)

        delta_bal_inr = round(bal_inr1 - bal_inr0, 2)

        return {
            "baseline_exchange_rate": e0,
            "depreciation_pct": depreciation_pct,
            "scenario_exchange_rate": e1,
            "baseline_exports_inr_crore": exp_inr0,
            "scenario_exports_inr_crore": exp_inr1,
            "baseline_imports_inr_crore": imp_inr0,
            "scenario_imports_inr_crore": imp_inr1,
            "baseline_trade_balance_inr_crore": bal_inr0,
            "scenario_trade_balance_inr_crore": bal_inr1,
            "delta_trade_balance_inr_crore": delta_bal_inr
        }

    @classmethod
    def simulate_export_demand_shock(
        cls,
        baseline: ShockBaseline,
        demand_shock_pct: float
    ) -> Dict[str, Any]:
        """Simulates global merchandise export demand shocks."""
        x0 = baseline.total_exports_usd_b
        x1 = round(x0 * (1.0 + demand_shock_pct / 100.0), 2)
        delta_x = round(x1 - x0, 2)

        return {
            "baseline_exports_usd_b": x0,
            "demand_shock_pct": demand_shock_pct,
            "scenario_exports_usd_b": x1,
            "delta_exports_usd_b": delta_x,
            "delta_exports_pct": demand_shock_pct
        }

    @classmethod
    def simulate_combined_scenario(
        cls,
        baseline: ShockBaseline,
        oil_price_shock_pct: float = 0.0,
        fx_depreciation_pct: float = 0.0,
        export_demand_shock_pct: float = 0.0,
        crude_demand_elasticity: float = 0.0,
        scenario_name: str = "Custom Scenario"
    ) -> Dict[str, Any]:
        """Executes full combined multi-factor shock with deterministic order of operations.
        
        Order of Operations:
        1. Calculate scenario crude oil import bill: M_oil(scenario)
        2. Hold non-oil imports constant: M_nonoil = baseline.non_oil_imports_usd_b
        3. Total scenario merchandise imports: M(scenario) = M_nonoil + M_oil(scenario)
        4. Calculate scenario merchandise exports: X(scenario) = X_baseline * (1 + export_shock / 100)
        5. Net Trade Balance in USD: TB(scenario) = X(scenario) - M(scenario)
        6. Compute Scenario Exchange Rate: e(scenario) = e_baseline * (1 + depr / 100)
        7. Convert Trade Balance to INR Crore: TB_INR(scenario) = TB(scenario) * e(scenario) * 100
        8. Compute net variances (Delta USD and Delta INR Crore)
        """
        # Step 1: Crude Oil Shock
        oil_res = cls.simulate_crude_oil_shock(baseline, oil_price_shock_pct, crude_demand_elasticity)
        m_oil_scenario = oil_res["scenario_oil_bill_usd_b"]
        delta_oil_usd = oil_res["delta_oil_bill_usd_b"]

        # Step 2 & 3: Total Imports
        m_total_scenario = round(baseline.non_oil_imports_usd_b + m_oil_scenario, 2)
        delta_imports_usd = round(m_total_scenario - baseline.total_imports_usd_b, 2)

        # Step 4: Export Demand Shock
        exp_res = cls.simulate_export_demand_shock(baseline, export_demand_shock_pct)
        x_scenario = exp_res["scenario_exports_usd_b"]
        delta_exports_usd = exp_res["delta_exports_usd_b"]

        # Step 5: Net Trade Balance in USD
        tb_scenario_usd = round(x_scenario - m_total_scenario, 2)
        delta_tb_usd = round(tb_scenario_usd - baseline.trade_balance_usd_b, 2)
        delta_tb_pct = round((delta_tb_usd / abs(baseline.trade_balance_usd_b)) * 100.0, 2) if baseline.trade_balance_usd_b != 0 else 0.0

        # Step 6: Exchange Rate
        fx_res = cls.simulate_exchange_rate_shock(baseline, fx_depreciation_pct)
        e_scenario = fx_res["scenario_exchange_rate"]

        # Step 7: INR Valuation
        tb_scenario_inr = round(EconomicDataContract.to_inr_crore(tb_scenario_usd, e_scenario), 2)
        delta_tb_inr = round(tb_scenario_inr - baseline.trade_balance_inr_crore, 2)

        # Step 8: Waterfall components breakdown
        waterfall = [
            {"step": "Baseline Trade Deficit", "value_usd_b": baseline.trade_balance_usd_b, "type": "baseline"},
            {"step": "Crude Oil Price Shock", "value_usd_b": -delta_oil_usd, "type": "component"},
            {"step": "Export Demand Shock", "value_usd_b": delta_exports_usd, "type": "component"},
            {"step": "Scenario Trade Balance", "value_usd_b": tb_scenario_usd, "type": "total"}
        ]

        # Rule-based economic interpretation
        assessment = cls._generate_scenario_assessment(
            delta_tb_usd=delta_tb_usd,
            delta_oil_usd=delta_oil_usd,
            delta_exports_usd=delta_exports_usd,
            fx_rate=e_scenario,
            fx_depr=fx_depreciation_pct,
            tb_scenario_usd=tb_scenario_usd
        )

        result_payload = {
            "scenario_name": scenario_name,
            "parameters": {
                "oil_price_shock_pct": oil_price_shock_pct,
                "fx_depreciation_pct": fx_depreciation_pct,
                "export_demand_shock_pct": export_demand_shock_pct,
                "crude_demand_elasticity": crude_demand_elasticity
            },
            "baseline": baseline.to_dict(),
            "results": {
                "scenario_crude_oil_bill_usd_b": m_oil_scenario,
                "delta_oil_bill_usd_b": delta_oil_usd,
                "scenario_total_imports_usd_b": m_total_scenario,
                "delta_imports_usd_b": delta_imports_usd,
                "scenario_total_exports_usd_b": x_scenario,
                "delta_exports_usd_b": delta_exports_usd,
                "baseline_trade_balance_usd_b": baseline.trade_balance_usd_b,
                "scenario_trade_balance_usd_b": tb_scenario_usd,
                "delta_trade_balance_usd_b": delta_tb_usd,
                "delta_trade_balance_pct": delta_tb_pct,
                "baseline_trade_balance_inr_crore": baseline.trade_balance_inr_crore,
                "scenario_trade_balance_inr_crore": tb_scenario_inr,
                "delta_trade_balance_inr_crore": delta_tb_inr,
                "scenario_exchange_rate": e_scenario
            },
            "waterfall": waterfall,
            "economic_assessment": assessment
        }

        # Provenance and contract enforcement
        provenance = EconomicDataContract.attach_provenance(
            result=result_payload,
            source="India Trade Intelligence Simulation Engine (MoPNG/PPAC, DGCI&S, RBI Baseline)",
            target_period=baseline.period_label,
            methodology="Mechanical macroeconomic scenario accounting with short-run price elasticity and exchange rate conversion."
        )

        return provenance

    @classmethod
    def _generate_scenario_assessment(
        cls,
        delta_tb_usd: float,
        delta_oil_usd: float,
        delta_exports_usd: float,
        fx_rate: float,
        fx_depr: float,
        tb_scenario_usd: float
    ) -> str:
        """Constructs an analytical explanation of the scenario transmission channels."""
        bullets = []

        if delta_tb_usd < -15.0:
            bullets.append(
                f"**Severe External Sector Strain**: Net merchandise trade deficit deteriorates by **USD {abs(delta_tb_usd):.1f} Billion**, "
                f"widening the deficit to **USD {abs(tb_scenario_usd):.1f} Billion**. This represents significant pressure on the Current Account Deficit (CAD)."
            )
        elif delta_tb_usd < 0:
            bullets.append(
                f"**Moderate Deficit Expansion**: Net trade balance weakens by **USD {abs(delta_tb_usd):.1f} Billion**."
            )
        elif delta_tb_usd > 15.0:
            bullets.append(
                f"**Substantial Terms-of-Trade Windfall**: Net trade balance improves by **USD {delta_tb_usd:.1f} Billion**, "
                "delivering significant foreign currency savings and easing external borrowing needs."
            )
        else:
            bullets.append(
                f"**Stable Trade Balance**: Net trade balance changes marginally by **USD {delta_tb_usd:+.1f} Billion**."
            )

        # Oil channel
        if delta_oil_usd > 10.0:
            bullets.append(
                f"**Energy Channel Dominance**: The crude oil import bill expands by **USD {delta_oil_usd:.1f} Billion**, "
                "highlighting India's acute terms-of-trade sensitivity to petroleum price spikes."
            )
        elif delta_oil_usd < -10.0:
            bullets.append(
                f"**Energy Windfall**: Lower crude prices generate **USD {abs(delta_oil_usd):.1f} Billion** in direct import bill savings."
            )

        # FX channel
        if fx_depr > 5.0:
            bullets.append(
                f"**Exchange Rate Pass-Through**: The Rupee settles at **{fx_rate:.2f} INR/USD** ({fx_depr:+.1f}% depreciation). "
                "While improving rupee earnings for exporters, it elevates landed costs of essential imports (crude, edible oils, fertilizer), "
                "stoking imported CPI inflation."
            )
        elif fx_depr < -2.0:
            bullets.append(
                f"**Rupee Appreciation**: Strengthening to **{fx_rate:.2f} INR/USD** dampens domestic landed costs of imports, "
                "though marginally compressing rupee-denominated export realizations."
            )

        # Export channel
        if delta_exports_usd < -10.0:
            bullets.append(
                f"**External Demand Drag**: Global demand contraction reduces export receipts by **USD {abs(delta_exports_usd):.1f} Billion**, "
                "impacting labour-intensive sectors such as textiles, gems & jewellery, and engineering goods."
            )

        return "\n\n".join(bullets)

    @classmethod
    def generate_sensitivity_grid(
        cls,
        baseline: ShockBaseline,
        oil_shocks: Optional[List[float]] = None,
        fx_shocks: Optional[List[float]] = None,
        export_shock: float = 0.0,
        crude_elasticity: float = 0.0
    ) -> pd.DataFrame:
        """Generates a 2D sensitivity matrix evaluating combinations of crude oil shocks vs INR/USD depreciation.
        Returns a DataFrame where rows = Crude Oil Shocks (%) and columns = INR Depreciation (%).
        Values represent Net Trade Balance Impact in USD Billion (Delta Trade Balance).
        """
        if oil_shocks is None:
            oil_shocks = [-30.0, -15.0, 0.0, 15.0, 30.0, 50.0]
        if fx_shocks is None:
            fx_shocks = [-5.0, 0.0, 5.0, 10.0, 15.0]

        matrix = {}
        for fx in fx_shocks:
            col_label = f"FX {fx:+g}% ({baseline.exchange_rate_inr_per_usd * (1 + fx / 100):.1f})"
            matrix[col_label] = []
            for oil in oil_shocks:
                res = cls.simulate_combined_scenario(
                    baseline=baseline,
                    oil_price_shock_pct=oil,
                    fx_depreciation_pct=fx,
                    export_demand_shock_pct=export_shock,
                    crude_demand_elasticity=crude_elasticity
                )
                delta_tb = res["results"]["delta_trade_balance_usd_b"]
                matrix[col_label].append(delta_tb)

        row_labels = [f"Crude {oil:+g}% (${baseline.crude_price_usd_per_bbl * (1 + oil / 100):.1f})" for oil in oil_shocks]
        df_grid = pd.DataFrame(matrix, index=row_labels)
        df_grid.index.name = "Crude Oil Shock"
        return df_grid

    @classmethod
    def compare_preset_scenarios(
        cls,
        baseline: ShockBaseline
    ) -> pd.DataFrame:
        """Executes all standard scenario presets and formats a multi-column comparison table."""
        rows = []
        for name, params in cls.PRESETS.items():
            res = cls.simulate_combined_scenario(
                baseline=baseline,
                oil_price_shock_pct=params["oil_price_shock_pct"],
                fx_depreciation_pct=params["fx_depreciation_pct"],
                export_demand_shock_pct=params["export_demand_shock_pct"],
                crude_demand_elasticity=params["crude_demand_elasticity"],
                scenario_name=name
            )
            r = res["results"]
            rows.append({
                "Scenario": name,
                "Crude Shock (%)": f"{params['oil_price_shock_pct']:+g}%",
                "INR/USD Depr (%)": f"{params['fx_depreciation_pct']:+g}%",
                "Export Shock (%)": f"{params['export_demand_shock_pct']:+g}%",
                "Crude Oil Bill ($B)": r["scenario_crude_oil_bill_usd_b"],
                "Total Exports ($B)": r["scenario_total_exports_usd_b"],
                "Total Imports ($B)": r["scenario_total_imports_usd_b"],
                "Trade Balance ($B)": r["scenario_trade_balance_usd_b"],
                "Deficit Change ($B)": r["delta_trade_balance_usd_b"],
                "Exchange Rate": r["scenario_exchange_rate"]
            })

        return pd.DataFrame(rows)

    @staticmethod
    def export_scenario_to_json(scenario_result: Dict[str, Any]) -> str:
        """Serializes scenario simulation payload into formatted JSON string."""
        return json.dumps(scenario_result, indent=2)

    @staticmethod
    def export_sensitivity_grid_to_csv(grid_df: pd.DataFrame) -> str:
        """Serializes 2D sensitivity grid DataFrame into CSV format."""
        return grid_df.to_csv(index=True)
