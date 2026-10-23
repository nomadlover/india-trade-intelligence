"""End-to-end data pipeline runner for India Trade Intelligence.
Orchestrates:
RAW DATA INGESTION -> VALIDATION -> CLEANING -> TRANSFORMATION -> SQLITE PERSISTENCE
"""
import sys
import logging
from pathlib import Path

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
    generate_monthly_trade
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PipelineRunner")

def run_full_pipeline(force_wb_refresh: bool = False):
    """Executes the complete research data pipeline with empirical auditing."""
    logger.info("==================================================")
    logger.info("STARTING INDIA TRADE INTELLIGENCE DATA PIPELINE")
    logger.info("==================================================")

    # 0. Ensure raw baseline files exist
    logger.info("STEP 0: Verifying Raw Government of India and RBI Datasets...")
    generate_bilateral_trade()
    generate_commodity_trade()
    generate_monthly_trade()

    # 1. Ingestion (World Bank API + DGCI&S + RBI)
    logger.info("STEP 1: Fetching Official Datasets (World Bank API + GoI Archives)...")
    fetcher = TradeDataFetcher()
    wb_payload = fetcher.fetch_all_world_bank_data(force_refresh=force_wb_refresh)
    df_raw_bilateral = fetcher.load_raw_dgcis_bilateral()
    df_raw_commodity = fetcher.load_raw_dgcis_commodities()
    df_raw_monthly = fetcher.load_raw_rbi_monthly()

    # 2. Validation
    logger.info("STEP 2: Executing Econometric and Schema Validation Suite...")
    val_wb = TradeDataValidator.validate_world_bank_payload(wb_payload)
    val_bilat = TradeDataValidator.validate_bilateral_trade(df_raw_bilateral)
    val_comm = TradeDataValidator.validate_commodity_trade(df_raw_commodity)
    val_month = TradeDataValidator.validate_monthly_trade(df_raw_monthly)

    logger.info(val_wb.summary())
    logger.info(val_bilat.summary())
    logger.info(val_comm.summary())
    logger.info(val_month.summary())

    if not (val_wb.is_valid and val_bilat.is_valid and val_comm.is_valid and val_month.is_valid):
        raise ValueError("Data pipeline validation failed. Terminating before transformation.")

    # 3. Cleaning & Standardization
    logger.info("STEP 3: Cleaning, Standardizing Currencies, and Aligning Dates...")
    cleaner = TradeDataCleaner()
    df_clean_macro = cleaner.clean_world_bank_payload(wb_payload)
    df_clean_bilateral = cleaner.clean_bilateral_trade(df_raw_bilateral)
    df_clean_commodity = cleaner.clean_commodity_trade(df_raw_commodity)
    df_clean_monthly = cleaner.clean_monthly_trade(df_raw_monthly)

    # 4. Analytical Transformations (CAGR, HHI, YoY %, Moving Averages)
    logger.info("STEP 4: Computing Analytical Transformations & Econometric Indices...")
    df_trans_macro = TradeDataTransformer.transform_macro_annual(df_clean_macro)
    df_trans_bilateral = TradeDataTransformer.transform_bilateral_trade(df_clean_bilateral)
    df_trans_commodity = TradeDataTransformer.transform_commodity_trade(df_clean_commodity)
    df_trans_monthly = TradeDataTransformer.transform_monthly_trade(df_clean_monthly)

    # 5. SQLite Persistence & Indexing
    logger.info("STEP 5: Persisting to Relational Database (SQLite) with Indexes...")
    storage = TradeDataStorage()
    storage.save_metadata_catalog()
    storage.save_dataframe("macro_annual", df_trans_macro)
    storage.save_dataframe("bilateral_trade", df_trans_bilateral)
    storage.save_dataframe("commodity_trade", df_trans_commodity)
    storage.save_dataframe("monthly_trade", df_trans_monthly)

    storage.log_pipeline_run(
        status="SUCCESS",
        datasets=["macro_annual", "bilateral_trade", "commodity_trade", "monthly_trade", "metadata_catalog"],
        notes="Full pipeline run executed with strict validation."
    )

    logger.info("==================================================")
    logger.info("DATA PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f"Database located at: {storage.db_path}")
    logger.info("==================================================")

if __name__ == "__main__":
    run_full_pipeline()
