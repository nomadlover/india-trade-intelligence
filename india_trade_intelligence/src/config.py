"""Configuration constants, file paths, and indicator metadata for India Trade Intelligence."""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
METADATA_DIR = DATA_DIR / "metadata"
DB_PATH = DATA_DIR / "trade_intelligence.db"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

# World Bank API Configuration
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/IND/indicator"
WORLD_BANK_INDICATORS = {
    "exports_gnfs": {
        "code": "NE.EXP.GNFS.CD",
        "name": "Exports of goods and services (current US$)",
        "unit": "USD",
        "category": "Trade"
    },
    "imports_gnfs": {
        "code": "NE.IMP.GNFS.CD",
        "name": "Imports of goods and services (current US$)",
        "unit": "USD",
        "category": "Trade"
    },
    "gdp_current_usd": {
        "code": "NY.GDP.MKTP.CD",
        "name": "GDP (current US$)",
        "unit": "USD",
        "category": "Macro"
    },
    "exchange_rate_inr_usd": {
        "code": "PA.NUS.FCRF",
        "name": "Official exchange rate (INR per USD)",
        "unit": "INR/USD",
        "category": "Macro"
    },
    "inflation_cpi_pct": {
        "code": "FP.CPI.TOTL.ZG",
        "name": "CPI Inflation (annual %)",
        "unit": "Percent",
        "category": "Macro"
    },
    "trade_pct_gdp": {
        "code": "NE.TRD.GNFS.ZS",
        "name": "Trade (% of GDP)",
        "unit": "Percent",
        "category": "Trade"
    },
    "merchandise_exports": {
        "code": "BX.GSR.MRCH.CD",
        "name": "Merchandise exports (current US$)",
        "unit": "USD",
        "category": "Trade"
    },
    "merchandise_imports": {
        "code": "BM.GSR.MRCH.CD",
        "name": "Merchandise imports (current US$)",
        "unit": "USD",
        "category": "Trade"
    }
}

# Standard Country ISO-3 Codes for India's Major Trading Partners
COUNTRY_ISO_MAP = {
    "United States": "USA",
    "China": "CHN",
    "United Arab Emirates": "ARE",
    "Saudi Arabia": "SAU",
    "Russia": "RUS",
    "Singapore": "SGP",
    "Iraq": "IRQ",
    "Indonesia": "IDN",
    "Netherlands": "NLD",
    "Germany": "DEU",
    "United Kingdom": "GBR",
    "Japan": "JPN",
    "South Korea": "KOR",
    "Hong Kong": "HKG",
    "Australia": "AUS",
    "Switzerland": "CHE",
    "Belgium": "BEL",
    "Malaysia": "MYS",
    "South Africa": "ZAF",
    "Vietnam": "VNM",
    "Italy": "ITA",
    "Qatar": "QAT",
    "Kuwait": "KWT",
    "Brazil": "BRA",
    "Thailand": "THA",
    "Bangladesh": "BGD",
    "France": "FRA",
    "Oman": "OMN",
    "Nepal": "NPL",
    "Turkey": "TUR"
}

# Major Commodity Sectors
COMMODITY_SECTORS = [
    "Petroleum Products (Refined)",
    "Crude Petroleum",
    "Electronic Goods (incl. Smartphones)",
    "Engineering Goods & Machinery",
    "Drugs & Pharmaceuticals",
    "Gems & Jewellery",
    "Gold & Precious Metals",
    "Organic & Inorganic Chemicals",
    "Agricultural & Allied Products",
    "Coal, Coke & Briquettes",
    "Readymade Garments & Textiles",
    "Iron & Steel and Articles"
]
