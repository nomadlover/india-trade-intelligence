"""Automated test suite for Module B: Trade Shock Simulator."""
import pytest
import json
import pandas as pd
import numpy as np

from india_trade_intelligence.src.analysis.shocks import (
    TradeShockSimulator,
    ShockBaseline
)


class TestTradeShockSimulator:
    """Verifies macroeconomic shock models, accounting identities, and elasticity parameters."""

    @pytest.fixture
    def calibrated_baseline(self):
        """Returns standard calibrated macroeconomic baseline."""
        return ShockBaseline(
            period_label="FY 2023-24 Calibrated Baseline",
            crude_price_usd_per_bbl=84.50,
            crude_volume_mmt=232.5,
            crude_import_bill_usd_b=144.0,
            non_oil_imports_usd_b=533.2,
            total_imports_usd_b=677.2,
            total_exports_usd_b=437.1,
            trade_balance_usd_b=-240.1,
            exchange_rate_inr_per_usd=83.50,
            trade_balance_inr_crore=-2004835.0  # -240.1 * 83.50 * 100
        )

    def test_zero_shock_baseline_equivalence(self, calibrated_baseline):
        """Guarantees that 0% shocks produce identical baseline outputs without drift."""
        sim = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=0.0,
            fx_depreciation_pct=0.0,
            export_demand_shock_pct=0.0,
            crude_demand_elasticity=0.0,
            scenario_name="Zero Shock Verification"
        )
        res = sim["results"]

        assert res["delta_oil_bill_usd_b"] == 0.0
        assert res["delta_exports_usd_b"] == 0.0
        assert res["delta_imports_usd_b"] == 0.0
        assert res["delta_trade_balance_usd_b"] == 0.0
        assert res["scenario_trade_balance_usd_b"] == calibrated_baseline.trade_balance_usd_b
        assert res["scenario_exchange_rate"] == calibrated_baseline.exchange_rate_inr_per_usd

    def test_crude_oil_price_shock_direction(self, calibrated_baseline):
        """Verifies directional correctness of oil price spikes and collapses."""
        # Positive oil shock (+25%)
        sim_pos = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=25.0
        )
        assert sim_pos["results"]["delta_oil_bill_usd_b"] > 0
        assert sim_pos["results"]["scenario_trade_balance_usd_b"] < calibrated_baseline.trade_balance_usd_b
        assert sim_pos["results"]["delta_trade_balance_usd_b"] < 0  # Deficit widened

        # Negative oil shock (-25%)
        sim_neg = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=-25.0
        )
        assert sim_neg["results"]["delta_oil_bill_usd_b"] < 0
        assert sim_neg["results"]["scenario_trade_balance_usd_b"] > calibrated_baseline.trade_balance_usd_b
        assert sim_neg["results"]["delta_trade_balance_usd_b"] > 0  # Deficit narrowed

    def test_crude_volume_elasticity_moderation(self, calibrated_baseline):
        """Ensures non-zero price elasticity dampens expenditure surge via quantity contraction."""
        # Pure mechanical (zero elasticity)
        sim_mech = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=30.0,
            crude_demand_elasticity=0.0
        )
        # Elastic response (elasticity = -0.10)
        sim_elas = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=30.0,
            crude_demand_elasticity=-0.10
        )

        bill_mech = sim_mech["results"]["scenario_crude_oil_bill_usd_b"]
        bill_elas = sim_elas["results"]["scenario_crude_oil_bill_usd_b"]

        assert bill_elas < bill_mech
        assert sim_elas["results"]["scenario_trade_balance_usd_b"] > sim_mech["results"]["scenario_trade_balance_usd_b"]

    def test_accounting_identity_consistency(self, calibrated_baseline):
        """Verifies fundamental balance-of-payments identity: Delta TB = Delta Exports - Delta Imports."""
        sim = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=18.0,
            fx_depreciation_pct=4.5,
            export_demand_shock_pct=-3.0
        )
        res = sim["results"]

        expected_delta_tb = round(res["delta_exports_usd_b"] - res["delta_imports_usd_b"], 2)
        assert res["delta_trade_balance_usd_b"] == expected_delta_tb

    def test_sensitivity_matrix_monotonicity(self, calibrated_baseline):
        """Ensures 2D grid exhibits monotonic deficit deterioration along crude oil price shocks."""
        oil_shocks = [-20.0, 0.0, 20.0, 40.0]
        fx_shocks = [0.0, 5.0, 10.0]
        
        grid_df = TradeShockSimulator.generate_sensitivity_grid(
            baseline=calibrated_baseline,
            oil_shocks=oil_shocks,
            fx_shocks=fx_shocks
        )

        assert grid_df.shape == (4, 3)

        # For any FX column, as oil shock increases, delta trade balance becomes more negative (deficit widens)
        for col in grid_df.columns:
            col_vals = grid_df[col].tolist()
            for i in range(len(col_vals) - 1):
                assert col_vals[i] > col_vals[i + 1]

    def test_preset_scenarios_comparison(self, calibrated_baseline):
        """Verifies preset comparison table returns all four standard scenarios."""
        df_presets = TradeShockSimulator.compare_preset_scenarios(calibrated_baseline)
        assert len(df_presets) == 4
        assert "Baseline (Zero Shock)" in df_presets["Scenario"].values
        assert "Severe Stagflation Crisis" in df_presets["Scenario"].values

    def test_serialization(self, calibrated_baseline):
        """Tests JSON and CSV serialization formatting."""
        sim = TradeShockSimulator.simulate_combined_scenario(
            baseline=calibrated_baseline,
            oil_price_shock_pct=15.0,
            scenario_name="Serialization Test"
        )
        json_output = TradeShockSimulator.export_scenario_to_json(sim)
        parsed = json.loads(json_output)
        assert parsed["scenario_name"] == "Serialization Test"
        assert "_provenance" in parsed

        grid_df = TradeShockSimulator.generate_sensitivity_grid(calibrated_baseline)
        csv_output = TradeShockSimulator.export_sensitivity_grid_to_csv(grid_df)
        assert "Crude Oil Shock" in csv_output
