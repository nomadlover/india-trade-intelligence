# 🌐 INDIA TRADE INTELLIGENCE
### Research-Grade Economics & International Trade Data Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit Dashboard](https://img.shields.io/badge/streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Validation](https://img.shields.io/badge/pipeline-validated-emerald.svg)]()
[![Tests](https://img.shields.io/badge/pytest-61%20passed-success.svg)]()
[![Data Sources](https://img.shields.io/badge/sources-WorldBank%20%7C%20DGCI%26S%20%7C%20RBI%20%7C%20PPAC-darkblue.svg)]()

---

> 🏛️ **DATA PROVENANCE & TEMPORAL AUDIT NOTICE (October 2026):**  
> This platform has been independently audited for economic data provenance, accounting identities, and temporal accuracy.  
> - **Verified Coverage Horizons:**
>   - *Annual BoP Series:* 1995–2024 (World Bank WDI)
>   - *Customs Bilateral & Commodities:* FY 2013-14 to FY 2023-24 (Final), FY 2024-25 Q1 (Provisional), FY 2025-26 (Interim)
>   - *High-Frequency Monthly Customs:* Jan 2018 – Feb 2026 (All 12 months of CY 2025 + Jan/Feb 2026 Quick Estimates)
>   - *Energy & Hydrocarbons:* 2010–2025 (PPAC / MoP&NG)
>   - *External Sector & Domestic Macro:* 1995–2025 (RBI DBIE / MoSPI)
>   - *Trading Partner Demand Conditions:* 2014–2025 (IMF WEO / Partner Central Banks)
> - **Strict Epistemic Mandate:** Historical benchmark data is strictly labeled with its explicit year and is never mischaracterized as "Today" or "Live". Non-existent or future periods trigger **explicit abstention**.

---

## 🎯 Executive Overview & Platform Mission

**INDIA TRADE INTELLIGENCE** is a research-grade economics application designed to analyze, model, and interpret India's foreign trade and macroeconomic dynamics through verified public datasets.

Rather than acting as a generic economics dashboard, this application enforces:
- **Price vs Quantity Decomposition**: Exact log-additive split $\Delta \ln(V) = \Delta \ln(P) + \Delta \ln(Q)$ separating unit value shifts from genuine physical volume changes across major exports and imports.
- **Energy & Hydrocarbon Vulnerability**: Real-world modeling of India's ~87% crude import dependence, Urals crude discounts against Brent, domestic export refining margins, and net petroleum import burden ($85.4B in 2024).
- **External Sector Resilience**: Monitoring India's $685B+ foreign exchange reserve buffer (~11.5 months import cover), Current Account Deficit (1.1% of GDP), and 40-currency REER.
- **Trading Partner Demand & Macro Transmission**: High-frequency tracking of economic growth, central bank policy rates, and manufacturing PMI across India's top 4 partners (US, China, UAE, EU).
- **Trade Policy & Geopolitical Event Timeline**: Catalog of 12 verified milestones (India-UAE CEPA, EFTA TEPA, PLI schemes, Red Sea routing disruptions, and agricultural export curbs).
- **Economic Risk Monitoring**: Real-time evaluation of partner/commodity HHI concentration and critical single-supplier import dependencies (APIs 68%, solar cells 62%, coking coal 52%, crude 36.8%).
- **Semi-Annual Automated Refresh Architecture**: Scheduled automated pipeline execution on **1 April** and **1 October** via GitHub Actions with fail-safe rollback to preserve the last-known-good dataset.
- **Epistemic AI Research Layer**: Strict 5-part taxonomy (**FACT**, **CALCULATION**, **INTERPRETATION**, **HYPOTHESIS**, **LIMITATIONS & UNKNOWNS**) with **mandatory explicit abstention** on unverified indicators.
- **High-Contrast Dark Theme**: All interactive Plotly figures rendered in high-contrast dark academic styling.

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
| **9. Price vs Quantity Decomposition** | Log-additive decomposition $\Delta \ln V = \Delta \ln P + \Delta \ln Q$ | Refined petroleum export contraction in FY24 was driven >100% by unit value price degradation (-17.2%) while volumes expanded (+4.2%). Smartphones showed simultaneous volume (+34.8%) and unit value (+6.1%) gains. |
| **10. Energy Terms of Trade Exposure** | Crack spread and net oil burden derivation | Gross crude imports ($132.8B) offset by refined product exports ($47.4B) yielded a net petroleum deficit of $85.4B, with Indian Basket crude averaging a $2.4/bbl discount to Brent. |
| **11. External Sector Buffers** | FX reserve import cover, CAD sustainability | FX reserves ($685B+) provide ~11.5 months of import cover, keeping India insulated from global monetary tightening. |
| **12. Partner Demand & Rate Cycles** | Destination GDP growth and PMI cross-correlation | Resilient US consumer demand (+2.8% GDP) bolstered electronics, while Eurozone industrial weakness (45.8 PMI) dampened textile shipments. |
| **13. Trade Policy & FTA Realignment** | Policy event timeline & bilateral flow tracking | India-UAE CEPA expanded bilateral volumes past $85B, while the Red Sea crisis imposed a 40–60% freight penalty and 12–18 day transit delay on European routes. |
| **14. Critical Import Vulnerabilities** | Single-supplier dependency calculation | High single-supplier concentration: APIs from China (68.0%), solar cells from China (62.0%), and coking coal from Australia (52.0%). |

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

---

## 🔄 Semi-Annual Automated Refresh Architecture

The platform implements an automated continuous data maintenance architecture:
- **Triggers**: Scheduled on **1 April** (FY close & Quick Estimates) and **1 October** (Mid-year DGCI&S revisions) at 00:00 UTC via GitHub Actions, with manual `workflow_dispatch` override.
- **Pipeline Workflow**: Fetches new releases → validates schemas & continuity → standardizes currencies & units → persists indexed SQLite tables → executes full 61-test verification suite → commits and pushes verified data.
- **Fail-Safe Rollback Protocol**: If an external source format or schema breaks, the runner logs `CRITICAL_FAILURE`, notifies maintainers, and **retains the last-known-good dataset** without publishing corrupt or partial data.

---

## 🧪 Comprehensive Automated Test Suite (61 Tests Passing)

The repository includes 61 automated unit and econometric audit tests executed via `pytest`:
1. **8 Expanded Intelligence Tests (`test_expanded_intelligence.py`)**:
   - Price vs Quantity log-additive decomposition identity ($\Delta \ln V = \Delta \ln P + \Delta \ln Q$)
   - Energy exposure, Indian basket crude discount, and net petroleum bill identities
   - External sector macro indicators (FX reserves import cover, CAD % GDP)
   - Key trading partner conditions (US, China, UAE, EU GDP, and manufacturing PMI)
   - Trade policy events catalog integrity (CEPA, TEPA, PLI, Red Sea)
   - Economic risk indicators (partner/commodity HHI and single-supplier dependencies)
   - AI assistant explicit abstention on unverified future years / out-of-scope queries
   - Expanded provenance registry completeness
2. **11 Economic Audit & Epistemic Tests (`test_audit.py`)**:
   - Provenance metadata completeness, absolute ban on misleading "today", CPI calculation gap protection, purchasing power decay, commodity basket benchmarks, trade balance identity, trade openness formula, Rule of 70 halving, pre/post-COVID structural shift, and AI fallback protection.
3. **18 Provisional Integrity & SEZ Reconciliation Tests (`test_provisional_integrity.py`)**:
   - 5-Tier duplicate transaction detection (`CONFIRMED_DUPLICATE`, `POTENTIAL_DUPLICATE`, `LEGITIMATE_REPEATED_TRANSACTION`, `UNRESOLVED`, `NOT_APPLICABLE_AGGREGATE_LEVEL`)
   - SEZ online vs ICEGATE customs reporting reconciliations
   - Multi-scenario annualisation bounds (observed, linear, seasonal, ±6% confidence interval)
   - Status propagation rules for combined merchandise and services trade
   - Source outage historical version retention
4. **24 Pipeline Transformation, Cleaning & Storage Tests**:
   - Storage schema validation, OLS trend fitting, structural break detection, causality disclaimers, currency conversions, ISO-3 country mappings, commodity chapter cleaning, and monthly regex validation.

---

## 🚀 Quickstart & Reproducibility Guide

```powershell
# 1. Clone repository
git clone https://github.com/nomadlover/india-trade-intelligence.git
cd india-trade-intelligence

# 2. Install verified dependencies
pip install -r requirements.txt

# 3. Execute the full multi-domain data pipeline
python india_trade_intelligence/run_pipeline.py

# 4. Run the 61-test verification suite
python -m pytest india_trade_intelligence/tests/ -v

# 5. Launch the interactive dashboard
streamlit run india_trade_intelligence/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.
