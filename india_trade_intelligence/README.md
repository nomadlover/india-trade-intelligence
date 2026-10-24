# 🌐 INDIA TRADE INTELLIGENCE
### Research-Grade Economics & International Trade Data Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit Dashboard](https://img.shields.io/badge/streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Validation](https://img.shields.io/badge/pipeline-validated-emerald.svg)]()
[![Tests](https://img.shields.io/badge/pytest-passed-success.svg)]()
[![Data Sources](https://img.shields.io/badge/sources-WorldBank%20%7C%20DGCI%26S%20%7C%20RBI-darkblue.svg)]()

---

> 🏛️ **DATA PROVENANCE & TEMPORAL AUDIT NOTICE (October 2026):**  
> This platform has been independently audited for economic data provenance, accounting identities, and temporal accuracy.  
> - **Latest Complete Annual Data:** Calendar Year 2024 (World Bank WDI) and Financial Year 2023-24 (DGCI&S).  
> - **Provisional Horizon:** FY 2024-25 Quarter 1 (April–July) momentum annualized/interim as reported in preliminary releases.  
> - **Strict Temporal Grounding:** Historical benchmark data (e.g. 2024) is strictly labeled with its explicit year and is never mischaracterized as "Today" or "Live".

---

## 🎯 Executive Overview & Research Goal

**INDIA TRADE INTELLIGENCE** is a research-grade economics application designed to analyze, model, and interpret India's foreign trade dynamics through verified public datasets.

Rather than acting as a generic economics dashboard, this application enforces:
- **Strict Empirical Data Engineering**: Multi-tier pipeline maintaining strict separation between raw and processed data.
- **Accurate & Real Story of the Indian Economy**: Grounded economic studies evaluating the Post-2020 export breakout, the Russian crude pivot, the Mobile PLI surge, and the services cushion.
- **Inflation & Real Purchasing Power**: Interactive simulator revealing the erosion in the real value of the Rupee and physical commodity purchasing power over 30 years (1995–2024).
- **Econometric Rigor**: OLS secular trend decomposition, Herfindahl-Hirschman (HHI) concentration indices, rolling volatility smoothing, and pre/post-COVID structural mean comparisons.
- **Epistemic AI Research Layer**: Outcomes partitioned into **FACT**, **CALCULATION**, **INTERPRETATION**, and **HYPOTHESIS**, with mathematical verification to eliminate numerical hallucinations.
- **Methodological Guardrails**: Explicit warnings preventing correlation-causation fallacies.
- **High-Contrast Dark Theme**: All interactive Plotly figures rendered in high-contrast dark styling with vivid text and map contrast.

---

## 🧭 Curated Empirical Research Inquiries Answered

| Curated Inquiry | Empirical Methodology | Real Economic Finding |
|---|---|---|
| **1. Post-2020 Export Breakout** | OLS secular trend, 10-Yr CAGR, Pre/Post-COVID break | Total exports crossed **$829.8B** (CY 2024), driven by high-value refined petroleum, smartphones, and pharmaceuticals (+53.2% post-COVID jump). |
| **2. Russian Oil Re-routing** | Bilateral shift, crude price discount tracking | Russia surged from under $4B pre-2022 to **$61.4B** in FY24, displacing traditional Gulf suppliers and boosting domestic refining crack spreads. |
| **3. Mobile & Electronics PLI** | Sectoral inflection curves, CAGR | Electronics exports jumped from $7.6B (FY18) to **$29.1B** (FY24) under the PLI scheme, though gross component imports remain high ($89.8B). |
| **4. Goods Deficit vs Services Surplus** | Net coverage ratio, BoP Current Account metrics | Persistent merchandise deficit (~$238B) is counterbalanced by software and professional services surpluses ($170B+), keeping net goods & services deficit at -$65.2B (~1.8% of GDP) and avoiding a BoP crisis. |
| **5. Currency Depreciation Paradox** | Pearson correlation, real vs nominal exchange rates | INR/USD depreciation from ₹32 (1995) to ₹84+ (2025) does not eliminate deficit because crude and components are price-inelastic. |
| **6. China Intermediate Dependence** | Bilateral coverage ratio, input decomposition | Deficit with China exceeds -$85B, concentrated in essential manufacturing inputs (APIs, solar cells, display panels) rather than consumer toys. |
| **7. Provisional FY 2024-25 Q1 Trajectory** | High-frequency monthly tracking, freight indices | Quarter 1 (April–July) data tracks exports toward ~$880B annualized despite Red Sea container route friction. |
| **8. Purchasing Power Erosion & Terms of Trade** | CPI index compounding, Rule of 70, real basket | The Rupee's domestic purchasing power halves every ~12.0 years at ~5.82% mean inflation; ₹1,000 from 2000 retains ~₹235 of goods purchasing capacity in 2024 benchmark terms. |

---

## 🛒 Inflation & Purchasing Power (Value of Your Money)

The platform features an interactive real-economy simulator answering: **"What is the real value of your money?"**

- **Cumulative CPI Compounding**: Derives India's price index with compounding annual inflation rates from 1995 to 2024 (30 annual observations).
- **Purchasing Power Retention**: Shows how much purchasing capacity remains from ₹100, ₹1,000, or ₹10,000 across decades.
- **Headline CPI vs Retail Price Benchmarks**:
  - *Headline CPI (MoSPI)*: Weighted representative basket of 299 goods and services.
  - *Representative Commodity Benchmarks (Documented Historical Retail Proxies)*:
    - 🌾 **Rice (Staple Food)**: ₹9.5/kg (1995) vs ₹60/kg (2024 benchmark) / ₹64/kg (2025 benchmark)
    - ⛽ **Petrol (Transport Energy)**: ₹18.0/L (1995) vs ₹97/L (2024 benchmark) / ₹98/L (2025 benchmark)
    - 🔥 **LPG Cylinder (14.2kg)**: ₹135 (1995) vs ₹850 (2024 benchmark) / ₹870 (2025 benchmark)
    - 🍲 **Wholesome Meal / Thali**: ₹10 (1995) vs ₹125 (2024 benchmark) / ₹135 (2025 benchmark)
    - 🎟️ **Cinema Ticket**: ₹15 (1995) vs ₹320 (2024 benchmark) / ₹350 (2025 benchmark)
    - 🪙 **24K Gold**: ₹468/g (1995) vs ₹7,200/g (2024 benchmark) / ₹7,800/g (2025 benchmark)

### Advanced Econometric Formulations:
1. **Purchasing Power Parity (PPP) & Real Exchange Rate:**
   $$RER = e \times \frac{P^*}{P}$$
2. **Real Terms of Trade (Real ToT):**
   $$ToT_{\text{real}} = \frac{P_x / P_{x,\text{base}}}{P_m / P_{m,\text{base}}} \times 100$$
3. **Rule of 70 for Approximate Currency Purchasing Power Halving:**
   $$T_{\text{half}} \approx \frac{70}{\bar{\pi}}$$
4. **Real Trade Valuation Deflator:**
   $$V_{\text{real}} = \frac{V_{\text{nominal}}}{\text{CPI} / 100}$$

---

## 📊 Data Pipeline Architecture

```mermaid
flowchart TD
    A["Raw Public Data Ingestion<br/>(World Bank REST API, DGCI&S, RBI)"] --> B["Strict Validation Suite<br/>(Accounting Identities, Schema, Ranges)"]
    B --> C["Data Cleaning & Standardization<br/>(Currencies: USD B / $M / INR Cr, ISO-3 Codes)"]
    C --> D["Analytical Transformations<br/>(CAGR, HHI, YoY %, CPI Index, 12M Rolling Trends)"]
    D --> E["Relational Persistence<br/>(Indexed SQLite Database & Processed CSVs)"]
    E --> F["Interactive High-Contrast Dashboard<br/>(Streamlit + Dark Plotly Visualizations)"]
    E --> G["AI-Powered Research Outcomes<br/>(FACT, CALCULATION, INTERPRETATION, HYPOTHESIS)"]
```

---

## 🏛️ Official Data Sources & Provenance Registry

| Metric Identifier | Official Source | Observation Horizon | Frequency | Measurement Unit | Accounting Definition | Data Status |
|---|---|---|---|---|---|---|
| `macro_exports_gnfs` | World Bank WDI (`NE.EXP.GNFS.CD`) | 1995–2024 | Calendar Year | Current US$ Billion | Goods and market services credits | Official Final |
| `macro_imports_gnfs` | World Bank WDI (`NE.IMP.GNFS.CD`) | 1995–2024 | Calendar Year | Current US$ Billion | Goods and market services debits | Official Final |
| `macro_trade_balance` | Derived Accounting Identity | 1995–2024 | Calendar Year | Current US$ Billion | Balance = Exports - Imports | Derived Identity |
| `macro_trade_openness` | Derived Econometric Ratio | 1995–2024 | Calendar Year | % of GDP | ((Exports + Imports) / GDP) * 100 | Derived Metric |
| `macro_cpi_inflation` | World Bank WDI (`FP.CPI.TOTL.ZG`) / MoSPI | 1995–2024 (30 obs) | Calendar Year | Annual % Change | Headline consumer price change | Official Final |
| `bilateral_merchandise_trade` | DGCI&S, Ministry of Commerce | FY14–FY24 (Final) / FY25 Q1 (Prov) | Financial Year | US$ Million / INR Cr | Customs physical merchandise | Official Final / Prov |
| `commodity_merchandise_trade` | DGCI&S, Ministry of Commerce | FY14–FY24 (Final) / FY25 Q1 (Prov) | Financial Year | US$ Million / INR Cr | 17 Principal sectors (ITC-HS) | Official Final / Prov |
| `monthly_merchandise_trade` | Reserve Bank of India (DBIE) | 2018–2025 | Monthly | US$ Million | Monthly customs merchandise | Official Monthly |
| `commodity_basket_benchmark` | Documented Retail Market Proxies | 1995–2025 Milestones | Quinquennial | INR per unit | Representative physical basket | Benchmark Proxy |
| `merchandise_exports_customs` | DGCI&S, Ministry of Commerce | FY14–FY24 (Final) / FY25 Q1 (Prov) | Monthly / Financial Year | Current US$ Billion | Physical border movement via customs ports | Official Final / Prov |
| `merchandise_imports_customs` | DGCI&S, Ministry of Commerce | FY14–FY24 (Final) / FY25 Q1 (Prov) | Monthly / Financial Year | Current US$ Billion | Physical inward movement via customs ports | Official Final / Prov |
| `services_exports_bop` | Reserve Bank of India (DBIE) | FY14–FY24 (Final) / FY25 Q1 (Prov) | Monthly / Quarterly BoP | Current US$ Billion | Cross-border invisibles receipts (FETERS) | Official Estimate / Reconciled |
| `services_imports_bop` | Reserve Bank of India (DBIE) | FY14–FY24 (Final) / FY25 Q1 (Prov) | Monthly / Quarterly BoP | Current US$ Billion | Cross-border invisibles payments (FETERS) | Official Estimate / Reconciled |
| `combined_goods_services_trade`| Ministry of Commerce / World Bank WDI | 1995–2024 / FY25 Q1 (Prov) | Annual / Financial Year | Current US$ Billion | Comprehensive goods + invisibles trade | Derived Composite Status |

---

## 🛡️ Provisional Data Integrity, SEZ Reconciliation & Revision Safeguards

To address the specific structural and statistical characteristics of Indian trade statistics, the platform implements dedicated integrity engines:

### 1. SEZ–ICEGATE Customs Reconciliation & 5-Tier Duplicate Detection (`TradeReconciliationEngine`)
* **SEZ Inclusion in Official Aggregates**: In official DGCI&S trade statistics, transactions of Special Economic Zone (SEZ) units are **included** in foreign trade aggregates. Physical goods exported from SEZs to foreign nations are national exports; foreign shipments landing in SEZs are national imports.
* **DTA Clearances Treatment**: Domestic Tariff Area (DTA) clearances (when an SEZ unit sells goods into domestic India) trigger customs duty payments on ICEGATE bills of entry. However, in national balance-of-payments accounts, DTA sales represent domestic inter-zone movements and are **excluded** from foreign trade totals.
* **5-Tier Duplicate Detection Taxonomy**:
  1. `CONFIRMED_DUPLICATE`: Identical primary transaction identifier (shipping bill or bill of entry number) with duplicate filing.
  2. `POTENTIAL_DUPLICATE`: Matching composite key (period, partner, commodity chapter, value) without unique ID to disambiguate. Flagged for review; **never silently dropped**.
  3. `LEGITIMATE_REPEATED_TRANSACTION`: Identical values, partners, and commodity chapters verified as distinct shipments via distinct declaration numbers or timestamps.
  4. `UNRESOLVED`: Ambiguous records during migration transitions.
  5. `NOT_APPLICABLE_AGGREGATE_LEVEL`: High-level aggregated tables (national totals or 2-digit HS chapters) where transaction-level deduplication is mathematically unsupported. The system explicitly discloses this data limitation.
* **Reconciliation Without Artificial Balancing**: Discrepancies between derived component sums and published reference totals are quantified and reported. The system strictly forbids artificial balancing plugs or unexplained adjustments.
* **Statistical Anomaly Review Signals**: Outliers detected via standard score or growth thresholds are flagged strictly as review signals requiring investigation, never as proof of data corruption.

### 2. Provisional Quick Estimates & Revision Tracking (`TradeRevisionTracker`)
* **Observation Lifecycle Tracking**: Follows official release statuses:  
  `PRELIMINARY` → `QUICK_ESTIMATE` → `PROVISIONAL` → `REVISED_PROVISIONAL` → `FINAL_RECONCILED`.
* **Full Version History Retention**: When updated figures are ingested, earlier versions are preserved in a chronological revision log recording release dates, version numbers, revision magnitudes, and percentage shifts.
* **Empirical Directionality**: Revisions are tracked bidirectionally without assuming systematic upward or downward bias.

### 3. Annualisation Safeguards & Uncertainty Bounds (`TradeAnnualisationEngine`)
* **Insufficient Data Guardrail**: Full-year extrapolations are **strictly refused** when fewer than 3 months of observations are available.
* **Multi-Scenario Modeling**: When annualised projections are generated (e.g., for FY 2024-25 Q1):
  - *Observed Volume to Date:* Exact verified empirical total ($144.1B for Apr–Jul exports).
  - *Simple Linear Extrapolation:* Baseline uniform monthly assumption ($432.3B).
  - *Seasonal Baseline Projection:* Incorporates historical empirical monthly weights (reflecting post-monsoon Q3-Q4 festive surge, ~$456.0B).
  - *Uncertainty Bounds:* Empirical confidence interval (±6%) reflecting terms-of-trade volatility ($428.6B – $483.4B).
* **Mandatory Research Disclaimer**: All annualised estimates are accompanied by explicit disclaimers identifying them as illustrative scenarios, not official government forecasts.

### 4. Separate Merchandise vs Services Trade Accounts & Status Propagation
* **Merchandise Trade (Customs Basis, DGCI&S)**: Physical cross-border commodity trade recorded FOB for exports and CIF for imports.
* **Services Trade (BoP Basis, RBI)**: Intangibles, software receipts, GCCs, and travel compiled via preliminary banking returns (FETERS) and finalized quarterly.
* **Status Propagation Rule**: When combined into aggregate trade, the composite metric inherits the lowest publication status among components. If merchandise is `PROVISIONAL` or services is `ESTIMATED`, the aggregate is strictly classified as `PROVISIONAL_COMPOSITE` and is **never** presented as final reconciled data.

### 5. Bilateral Mirror Trade & Transit Lag Semantics
* **Valuation Basis**: Exporter statistics are recorded FOB (port of exit); importer statistics are recorded CIF (port of arrival, ~8–12% higher due to freight and insurance).
* **Transit Lags**: Ocean shipping introduces 2 to 6 weeks of transit delay, naturally shifting recording across consecutive months between trading partners.

---

## 🧪 Comprehensive Automated Test Suite (53 Tests Passing)

The repository includes 53 automated unit and econometric audit tests executed via `pytest`:
1. **11 Economic Audit & Epistemic Tests (`test_audit.py`)**: Provenance metadata completeness, absolute ban on misleading "today", CPI calculation gap protection, purchasing power decay, commodity basket benchmarks, trade balance identity, trade openness formula, Rule of 70 halving, pre/post-COVID structural shift, and AI fallback protection.
2. **18 Provisional Integrity & SEZ Reconciliation Tests (`test_provisional_integrity.py`)**:
   - Duplicate transaction identifiers (`CONFIRMED_DUPLICATE`)
   - Legitimate repeated transactions with similar values (`LEGITIMATE_REPEATED_TRANSACTION`)
   - Candidate duplicates without transaction IDs (flagged for review, not dropped)
   - Unreconciled data compared with official aggregates (no artificial balancing)
   - Source totals differing due to reporting definitions (`STRUCTURAL_DEFINITION_DIFFERENCE`)
   - Preliminary observation subsequently revised (magnitude and direction tracked)
   - Preservation of historical versions (version trail preserved)
   - Partial-year compared with complete year (comparability warnings)
   - Annualisation of insufficient monthly data (refused if $N < 3$; linear vs seasonal bounds)
   - Merchandise combined with estimated services (composite status propagation)
   - Different reporting periods across components (mismatches detected)
   - Missing source publication status (assigned `UNKNOWN_STATUS`)
   - Documented data-quality warning (conditional generation)
   - Clean dataset displaying no unsupported warnings (no false alarms)
   - Bilateral reporting lags (transit delay + CIF/FOB markup)
   - Suspected anomaly as a review signal, not proof of error
   - AI-generated analysis acknowledging provisional/estimated data
   - Source outage preserving validated historical data
3. **24 Pipeline Transformation, Cleaning & Validation Tests**: Storage schema, OLS trend fitting, structural break detection, causality disclaimers, currency conversions, ISO-3 country mappings, commodity chapter cleaning, and monthly regex validation.

---

---

## 🚀 Quickstart & Reproducibility Guide

```powershell
# 1. Navigate to workspace
cd "india_trade_intelligence"

# 2. Run the Data Pipeline
python run_pipeline.py

# 3. Run all Tests (including Data Audit Suite)
python -m pytest tests -v

# 4. Launch the Dashboard
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.
