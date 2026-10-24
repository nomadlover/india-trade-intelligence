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

            # Data snapshots table for historical revision tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_version_id TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    observation_key TEXT NOT NULL,
                    indicator_id TEXT NOT NULL,
                    partner_country TEXT,
                    trade_flow TEXT,
                    reporting_period TEXT NOT NULL,
                    period_type TEXT NOT NULL,
                    original_value REAL,
                    normalised_value REAL,
                    original_unit TEXT,
                    normalised_unit TEXT,
                    retrieval_timestamp TEXT NOT NULL,
                    source_release_date TEXT,
                    data_status TEXT NOT NULL,
                    pipeline_version TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    UNIQUE(snapshot_version_id, observation_key)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_ver ON data_snapshots(snapshot_version_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_obs ON data_snapshots(observation_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_period ON data_snapshots(reporting_period)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_dataset ON data_snapshots(dataset_id)")

            # Revision records table comparing successive snapshot versions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revision_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    revision_id TEXT UNIQUE NOT NULL,
                    observation_key TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    indicator_id TEXT NOT NULL,
                    reporting_period TEXT NOT NULL,
                    previous_version_id TEXT NOT NULL,
                    new_version_id TEXT NOT NULL,
                    previous_value REAL,
                    new_value REAL,
                    absolute_revision REAL,
                    percentage_revision REAL,
                    previous_status TEXT,
                    new_status TEXT,
                    revision_classification TEXT NOT NULL,
                    revision_reason TEXT,
                    detected_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_key ON revision_records(observation_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_class ON revision_records(revision_classification)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_versions ON revision_records(previous_version_id, new_version_id)")

            # Revision and data-quality alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revision_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    revision_id TEXT,
                    observation_key TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    indicator_id TEXT NOT NULL,
                    reporting_period TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    threshold_value REAL,
                    actual_change REAL,
                    message TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_sev ON revision_alerts(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_period ON revision_alerts(reporting_period)")

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
            elif table_name == "commodity_price_quantity":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pq_fy ON commodity_price_quantity(financial_year)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pq_comm ON commodity_price_quantity(commodity_group)")
            elif table_name == "energy_commodity_exposure":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_year ON energy_commodity_exposure(year)")
            elif table_name == "external_sector_macro":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ext_year ON external_sector_macro(year)")
            elif table_name == "trading_partner_conditions":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_partner_year ON trading_partner_conditions(year)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_partner_name ON trading_partner_conditions(partner_name)")
            elif table_name == "trade_policy_events":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_cat ON trade_policy_events(category)")
            elif table_name == "commodity_partner_trade":
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpt_fy ON commodity_partner_trade(financial_year)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpt_comm ON commodity_partner_trade(commodity_group)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpt_flow ON commodity_partner_trade(trade_flow)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpt_partner ON commodity_partner_trade(partner_country)")

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

    def get_commodity_price_quantity(self, financial_year: Optional[str] = None) -> pd.DataFrame:
        """Retrieves commodity price, quantity, and unit-value decomposition data."""
        query = "SELECT * FROM commodity_price_quantity WHERE 1=1"
        params = []
        if financial_year:
            query += " AND financial_year = ?"
            params.append(financial_year)
        query += " ORDER BY fy_start_year ASC, value_usd_million DESC"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_energy_commodity_exposure(self) -> pd.DataFrame:
        """Retrieves energy, crude benchmarks, and strategic commodity exposure metrics."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM energy_commodity_exposure ORDER BY year ASC", conn)

    def get_external_sector_macro(self) -> pd.DataFrame:
        """Retrieves external sector (FX, CAD, debt, remittances) and domestic macro metrics."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM external_sector_macro ORDER BY year ASC", conn)

    def get_trading_partner_conditions(self, partner_name: Optional[str] = None) -> pd.DataFrame:
        """Retrieves trading partner macroeconomic conditions."""
        query = "SELECT * FROM trading_partner_conditions WHERE 1=1"
        params = []
        if partner_name:
            query += " AND partner_name = ?"
            params.append(partner_name)
        query += " ORDER BY year ASC"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_trade_policy_events(self, category: Optional[str] = None) -> pd.DataFrame:
        """Retrieves structured trade policy and geopolitical events catalog."""
        query = "SELECT * FROM trade_policy_events WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY effective_date DESC"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_commodity_partner_trade(
        self,
        financial_year: Optional[str] = None,
        commodity_group: Optional[str] = None,
        trade_flow: Optional[str] = None
    ) -> pd.DataFrame:
        """Retrieves commodity-by-partner bilateral trade data with optional filters."""
        query = "SELECT * FROM commodity_partner_trade WHERE 1=1"
        params = []
        if financial_year:
            query += " AND financial_year = ?"
            params.append(financial_year)
        if commodity_group:
            query += " AND commodity_group = ?"
            params.append(commodity_group)
        if trade_flow:
            query += " AND trade_flow = ?"
            params.append(trade_flow)
        query += " ORDER BY value_usd_million DESC"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_latest_refresh_status(self) -> Dict[str, Any]:
        """Returns metadata regarding the latest automated pipeline execution."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_execution_log ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                "executed_at": "Never",
                "status": "UNINITIALIZED",
                "datasets_updated": "None",
                "notes": "No pipeline run recorded."
            }

    # =====================================================================
    # DATA REVISION OBSERVATORY STORAGE METHODS
    # =====================================================================

    def save_data_snapshots(self, snapshots: List[Dict[str, Any]]):
        """Persists a list of versioned observation snapshots with deduplication."""
        if not snapshots:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO data_snapshots (
                    snapshot_version_id, dataset_id, source_id, observation_key,
                    indicator_id, partner_country, trade_flow, reporting_period,
                    period_type, original_value, normalised_value, original_unit,
                    normalised_unit, retrieval_timestamp, source_release_date,
                    data_status, pipeline_version, validation_status
                ) VALUES (
                    :snapshot_version_id, :dataset_id, :source_id, :observation_key,
                    :indicator_id, :partner_country, :trade_flow, :reporting_period,
                    :period_type, :original_value, :normalised_value, :original_unit,
                    :normalised_unit, :retrieval_timestamp, :source_release_date,
                    :data_status, :pipeline_version, :validation_status
                )
            """, snapshots)
            conn.commit()
            logger.info(f"Persisted {len(snapshots)} observation snapshots to 'data_snapshots'.")

    def get_snapshots(
        self,
        snapshot_version_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        indicator_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Retrieves snapshots matching optional filters."""
        query = "SELECT * FROM data_snapshots WHERE 1=1"
        params = []
        if snapshot_version_id:
            query += " AND snapshot_version_id = ?"
            params.append(snapshot_version_id)
        if dataset_id:
            query += " AND dataset_id = ?"
            params.append(dataset_id)
        if indicator_id:
            query += " AND indicator_id = ?"
            params.append(indicator_id)
        query += " ORDER BY reporting_period ASC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_available_snapshot_versions(self) -> List[str]:
        """Returns ordered list of distinct snapshot version identifiers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT snapshot_version_id FROM data_snapshots ORDER BY id ASC")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def save_revision_records(self, revisions: List[Dict[str, Any]]):
        """Persists detected revision records between successive snapshot versions."""
        if not revisions:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO revision_records (
                    revision_id, observation_key, dataset_id, indicator_id,
                    reporting_period, previous_version_id, new_version_id,
                    previous_value, new_value, absolute_revision, percentage_revision,
                    previous_status, new_status, revision_classification,
                    revision_reason, detected_at
                ) VALUES (
                    :revision_id, :observation_key, :dataset_id, :indicator_id,
                    :reporting_period, :previous_version_id, :new_version_id,
                    :previous_value, :new_value, :absolute_revision, :percentage_revision,
                    :previous_status, :new_status, :revision_classification,
                    :revision_reason, :detected_at
                )
            """, revisions)
            conn.commit()
            logger.info(f"Persisted {len(revisions)} revision records to 'revision_records'.")

    def get_revision_records(
        self,
        dataset_id: Optional[str] = None,
        classification: Optional[str] = None
    ) -> pd.DataFrame:
        """Retrieves revision comparison records with optional filters."""
        query = "SELECT * FROM revision_records WHERE 1=1"
        params = []
        if dataset_id:
            query += " AND dataset_id = ?"
            params.append(dataset_id)
        if classification:
            query += " AND revision_classification = ?"
            params.append(classification)
        query += " ORDER BY detected_at DESC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def save_revision_alerts(self, alerts: List[Dict[str, Any]]):
        """Persists data quality and revision threshold alerts."""
        if not alerts:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO revision_alerts (
                    alert_id, revision_id, observation_key, dataset_id,
                    indicator_id, reporting_period, alert_type, severity,
                    threshold_value, actual_change, message, triggered_at, status
                ) VALUES (
                    :alert_id, :revision_id, :observation_key, :dataset_id,
                    :indicator_id, :reporting_period, :alert_type, :severity,
                    :threshold_value, :actual_change, :message, :triggered_at, :status
                )
            """, alerts)
            conn.commit()
            logger.info(f"Persisted {len(alerts)} alerts to 'revision_alerts'.")

    def get_revision_alerts(self, severity: Optional[str] = None) -> pd.DataFrame:
        """Retrieves revision alerts with optional severity filter."""
        query = "SELECT * FROM revision_alerts WHERE 1=1"
        params = []
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        query += " ORDER BY triggered_at DESC"

        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

