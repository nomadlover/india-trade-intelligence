"""Storage module managing SQLite database operations and processed data persistence.
Provides high-performance relational queries and schema migrations.
"""
import sqlite3
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from india_trade_intelligence.src.config import (
    DB_PATH,
    PROCESSED_DATA_DIR,
    METADATA_DIR
)

logger = logging.getLogger(__name__)

class TradeDataStorage:
    """Manages SQLite storage, table indexing, and data retrieval."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns SQLite database connection with row factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db_schema(self):
        """Initializes tables, primary keys, and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Pipeline execution log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    executed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    datasets_updated TEXT NOT NULL,
                    notes TEXT
                )
            """)

            # Metadata catalog table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata_catalog (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    publisher TEXT NOT NULL,
                    url TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    coverage TEXT NOT NULL,
                    retrieval_date TEXT NOT NULL,
                    series_json TEXT NOT NULL
                )
            """)

            conn.commit()

    def save_metadata_catalog(self, catalog_path: Optional[Path] = None):
        """Loads and persists JSON data catalog into SQLite."""
        if catalog_path is None:
            catalog_path = METADATA_DIR / "data_catalog.json"
        
        if not catalog_path.exists():
            logger.warning(f"Metadata catalog not found at {catalog_path}")
            return

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        sources = catalog.get("sources", [])
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for src in sources:
                cursor.execute("""
                    INSERT OR REPLACE INTO metadata_catalog (
                        source_id, name, publisher, url, frequency, coverage, retrieval_date, series_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    src["id"],
                    src["name"],
                    src["publisher"],
                    src["url"],
                    src["frequency"],
                    src["coverage"],
                    src["retrieval_date"],
                    json.dumps(src.get("series", []))
                ))
            conn.commit()
            logger.info("Metadata catalog persisted to SQLite database.")

    def save_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "replace"):
        """Stores pandas DataFrame into SQLite table with automatic indexing."""
        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            cursor = conn.cursor()

            # Create strategic indexes for fast dashboard filtering
            if table_name == "bilateral_trade":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilateral_fy ON bilateral_trade(financial_year)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilateral_country ON bilateral_trade(country)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bilateral_iso3 ON bilateral_trade(iso3)")
            elif table_name == "commodity_trade":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_commodity_fy ON commodity_trade(financial_year)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_commodity_flow ON commodity_trade(trade_flow)")
            elif table_name == "macro_annual":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_macro_year ON macro_annual(year)")
            elif table_name == "monthly_trade":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_period ON monthly_trade(period)")

            conn.commit()
            logger.info(f"Persisted {len(df)} rows to table '{table_name}' with indexes.")

    def log_pipeline_run(self, status: str, datasets: List[str], notes: str = ""):
        """Records an audit log entry for the data pipeline."""
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pipeline_execution_log (executed_at, status, datasets_updated, notes)
                VALUES (?, ?, ?, ?)
            """, (now, status, ", ".join(datasets), notes))
            conn.commit()

    def get_macro_annual(self) -> pd.DataFrame:
        """Retrieves cleaned and transformed macro annual series."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM macro_annual ORDER BY year ASC", conn)

    def get_bilateral_trade(self, financial_year: Optional[str] = None, country: Optional[str] = None) -> pd.DataFrame:
        """Retrieves bilateral partner trade with optional filters."""
        query = "SELECT * FROM bilateral_trade WHERE 1=1"
        params = []
        if financial_year:
            query += " AND financial_year = ?"
            params.append(financial_year)
        if country:
            query += " AND country = ?"
            params.append(country)
        query += " ORDER BY total_trade_usd_million DESC"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_commodity_trade(self, financial_year: Optional[str] = None, flow: Optional[str] = None) -> pd.DataFrame:
        """Retrieves commodity group trade with optional filters."""
        query = "SELECT * FROM commodity_trade WHERE 1=1"
        params = []
        if financial_year:
            query += " AND financial_year = ?"
            params.append(financial_year)
        if flow:
            query += " AND trade_flow = ?"
            params.append(flow)
        query += " ORDER BY value_usd_million DESC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_monthly_trade(self) -> pd.DataFrame:
        """Retrieves monthly high-frequency merchandise trade series."""
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM monthly_trade ORDER BY period ASC", conn)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df

    def get_metadata_catalog(self) -> List[Dict[str, Any]]:
        """Retrieves source metadata catalog."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM metadata_catalog")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
