"""Tests for SQLite database storage, indexing, and data retrieval."""
import pytest
import sqlite3
import pandas as pd
from pathlib import Path
from india_trade_intelligence.src.pipeline.storage import TradeDataStorage

def test_sqlite_storage(tmp_path: Path):
    test_db = tmp_path / "test_trade.db"
    storage = TradeDataStorage(db_path=test_db)

    # Test saving DataFrame
    df = pd.DataFrame([
        {"year": 2023, "exports_usd_billion": 778.2, "imports_usd_billion": 853.5, "trade_balance_usd_billion": -75.3},
        {"year": 2024, "exports_usd_billion": 829.8, "imports_usd_billion": 895.0, "trade_balance_usd_billion": -65.2}
    ])
    storage.save_dataframe("macro_annual", df)

    retrieved = storage.get_macro_annual()
    assert len(retrieved) == 2
    assert retrieved.loc[1, "year"] == 2024
    assert retrieved.loc[1, "exports_usd_billion"] == 829.8

    # Test pipeline execution log
    storage.log_pipeline_run("SUCCESS", ["macro_annual"], "Unit test log")
    with storage.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, datasets_updated FROM pipeline_execution_log")
        row = cursor.fetchone()
        assert row["status"] == "SUCCESS"
        assert row["datasets_updated"] == "macro_annual"
