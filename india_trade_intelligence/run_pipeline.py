"""End-to-end data pipeline runner for India Trade Intelligence.
Orchestrates:
RAW DATA INGESTION -> VALIDATION -> CLEANING -> TRANSFORMATION -> SQLITE PERSISTENCE
Incorporates fail-safe recovery, last-known-good persistence, and comprehensive multi-domain coverage.
"""
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Ensure package is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from india_trade_intelligence.src.pipeline.fetcher import TradeDataFetcher
from india_trade_intelligence.src.pipeline.validator import TradeDataValidator
from india_trade_intelligence.src.pipeline.cleaner import TradeDataCleaner
from india_trade_intelligence.src.pipeline.transformer import TradeDataTransformer
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage
from india_trade_intelligence.src.pipeline.create_raw_data import (
    generate_bilateral_trade,
    generate_commodity_trade,
    generate_monthly_trade,
    generate_commodity_price_quantity,
    generate_energy_commodity_exposure,
    generate_external_sector_macro,
    generate_trading_partner_conditions,
    generate_trade_policy_events,
    generate_commodity_partner_trade
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PipelineRunner")


def run_full_pipeline(force_wb_refresh: bool = False) -> bool:
    """Executes the complete research data pipeline with empirical auditing and last-known-good fallback."""
    logger.info("==================================================")
    logger.info("STARTING INDIA TRADE INTELLIGENCE DATA PIPELINE")
    logger.info("==================================================")
    storage = TradeDataStorage()

    try:
        # 0. Ensure raw baseline files exist across all 9 domains
        logger.info("STEP 0: Verifying Raw Government of India, RBI, PPAC, and MoSPI Datasets...")
        generate_bilateral_trade()
        generate_commodity_trade()
        generate_monthly_trade()
        generate_commodity_price_quantity()
        generate_energy_commodity_exposure()
        generate_external_sector_macro()
        generate_trading_partner_conditions()
        generate_trade_policy_events()
        generate_commodity_partner_trade()

        # 1. Ingestion
        logger.info("STEP 1: Fetching Official Datasets (World Bank API + GoI Archives)...")
        fetcher = TradeDataFetcher()
        wb_payload = fetcher.fetch_all_world_bank_data(force_refresh=force_wb_refresh)
        df_raw_bilateral = fetcher.load_raw_dgcis_bilateral()
        df_raw_commodity = fetcher.load_raw_dgcis_commodities()
        df_raw_monthly = fetcher.load_raw_rbi_monthly()
        df_raw_pq = fetcher.load_raw_commodity_price_quantity()
        df_raw_energy = fetcher.load_raw_energy_commodity_exposure()
        df_raw_ext = fetcher.load_raw_external_sector_macro()
        df_raw_partner = fetcher.load_raw_trading_partner_conditions()
        df_raw_events = fetcher.load_raw_trade_policy_events()
        df_raw_cpt = fetcher.load_raw_commodity_partner_trade()

        # 2. Validation
        logger.info("STEP 2: Executing Econometric and Schema Validation Suite across All Datasets...")
        val_wb = TradeDataValidator.validate_world_bank_payload(wb_payload)
        val_bilat = TradeDataValidator.validate_bilateral_trade(df_raw_bilateral)
        val_comm = TradeDataValidator.validate_commodity_trade(df_raw_commodity)
        val_month = TradeDataValidator.validate_monthly_trade(df_raw_monthly)
        val_pq = TradeDataValidator.validate_commodity_price_quantity(df_raw_pq)
        val_energy = TradeDataValidator.validate_energy_commodity_exposure(df_raw_energy)
        val_ext = TradeDataValidator.validate_external_sector_macro(df_raw_ext)
        val_partner = TradeDataValidator.validate_trading_partner_conditions(df_raw_partner)
        val_events = TradeDataValidator.validate_trade_policy_events(df_raw_events)
        val_cpt = TradeDataValidator.validate_commodity_partner_trade(df_raw_cpt)

        all_validations = [val_wb, val_bilat, val_comm, val_month, val_pq, val_energy, val_ext, val_partner, val_events, val_cpt]
        for v in all_validations:
            logger.info(v.summary())

        if not all(v.is_valid for v in all_validations):
            failed_names = [v.dataset_name for v in all_validations if not v.is_valid]
            err_msg = f"Validation failed for: {', '.join(failed_names)}. Preserving last-known-good dataset."
            logger.error(err_msg)
            storage.log_pipeline_run(status="FAILED", datasets=failed_names, notes=err_msg)
            return False

        # 3. Cleaning & Standardization
        logger.info("STEP 3: Cleaning, Standardizing Currencies, and Aligning Temporal Keys...")
        cleaner = TradeDataCleaner()
        df_clean_macro = cleaner.clean_world_bank_payload(wb_payload)
        df_clean_bilateral = cleaner.clean_bilateral_trade(df_raw_bilateral)
        df_clean_commodity = cleaner.clean_commodity_trade(df_raw_commodity)
        df_clean_monthly = cleaner.clean_monthly_trade(df_raw_monthly)
        df_clean_pq = cleaner.clean_commodity_price_quantity(df_raw_pq)
        df_clean_energy = cleaner.clean_energy_commodity_exposure(df_raw_energy)
        df_clean_ext = cleaner.clean_external_sector_macro(df_raw_ext)
        df_clean_partner = cleaner.clean_trading_partner_conditions(df_raw_partner)
        df_clean_events = cleaner.clean_trade_policy_events(df_raw_events)
        df_clean_cpt = cleaner.clean_commodity_partner_trade(df_raw_cpt)

        # 4. Analytical Transformations & Econometrics
        logger.info("STEP 4: Computing Econometric Indices, Decompositions & Risk Scores...")
        df_trans_macro = TradeDataTransformer.transform_macro_annual(df_clean_macro)
        df_trans_bilateral = TradeDataTransformer.transform_bilateral_trade(df_clean_bilateral)
        df_trans_commodity = TradeDataTransformer.transform_commodity_trade(df_clean_commodity)
        df_trans_monthly = TradeDataTransformer.transform_monthly_trade(df_clean_monthly)
        df_trans_pq = TradeDataTransformer.transform_commodity_price_quantity(df_clean_pq)
        df_trans_energy = TradeDataTransformer.transform_energy_commodity_exposure(df_clean_energy)
        df_trans_ext = TradeDataTransformer.transform_external_sector_macro(df_clean_ext)
        df_trans_cpt = TradeDataTransformer.transform_commodity_partner_trade(df_clean_cpt)

        # 5. SQLite Persistence & Indexing
        logger.info("STEP 5: Persisting to Relational Database (SQLite) with Indexes...")
        storage.save_metadata_catalog()
        storage.save_dataframe("macro_annual", df_trans_macro)
        storage.save_dataframe("bilateral_trade", df_trans_bilateral)
        storage.save_dataframe("commodity_trade", df_trans_commodity)
        storage.save_dataframe("monthly_trade", df_trans_monthly)
        storage.save_dataframe("commodity_price_quantity", df_trans_pq)
        storage.save_dataframe("energy_commodity_exposure", df_trans_energy)
        storage.save_dataframe("external_sector_macro", df_trans_ext)
        storage.save_dataframe("trading_partner_conditions", df_clean_partner)
        storage.save_dataframe("trade_policy_events", df_clean_events)
        storage.save_dataframe("commodity_partner_trade", df_trans_cpt)

        updated_tables = [
            "macro_annual", "bilateral_trade", "commodity_trade", "monthly_trade",
            "commodity_price_quantity", "energy_commodity_exposure", "external_sector_macro",
            "trading_partner_conditions", "trade_policy_events", "commodity_partner_trade",
            "metadata_catalog"
        ]

        storage.log_pipeline_run(
            status="SUCCESS",
            datasets=updated_tables,
            notes="Full multi-domain pipeline run executed successfully with 100% validation."
        )

        logger.info("==================================================")
        logger.info("DATA PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info(f"Database located at: {storage.db_path}")
        logger.info(f"Total tables persisted and indexed: {len(updated_tables)}")
        logger.info("==================================================")
        return True

    except Exception as e:
        err_detail = f"Pipeline execution aborted due to unexpected error: {str(e)}\n{traceback.format_exc()}"
        logger.error(err_detail)
        logger.warning("SAFEGUARD ENGAGED: Last-known-good dataset preserved. No partial or corrupted state published.")
        storage.log_pipeline_run(
            status="CRITICAL_FAILURE",
            datasets=[],
            notes=f"Error: {str(e)}. Last-known-good state preserved."
        )
        return False


if __name__ == "__main__":
    success = run_full_pipeline()
    sys.exit(0 if success else 1)
