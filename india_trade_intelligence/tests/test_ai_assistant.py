"""Tests for AI-Powered Research Outcomes epistemic taxonomy, fact guardrails, and curated questions."""
from india_trade_intelligence.src.ai.assistant import TradeAIAssistant, RESEARCH_QUESTIONS_CATALOG

def test_ai_assistant_epistemic_taxonomy():
    assistant = TradeAIAssistant(api_key=None) # Tests offline deterministic expert engine
    mock_stats = {
        "latest_year": 2024,
        "latest_exports_usd_b": 829.8,
        "latest_imports_usd_b": 895.0,
        "latest_trade_balance_usd_b": -65.2,
        "export_cagr_10yr": 5.9,
        "top_export_partner": "United States",
        "top_import_partner": "China",
        "top_export_commodity": "Petroleum Products (Refined)",
        "top_import_commodity": "Crude Petroleum"
    }

    # Query 1: Post-2020 Export Breakout
    q1 = RESEARCH_QUESTIONS_CATALOG[0]
    res1 = assistant.query(q1, mock_stats)
    assert "plain_summary" in res1
    assert "fact" in res1
    assert "calculation" in res1
    assert "interpretation" in res1
    assert "hypothesis" in res1
    assert "further_investigation" in res1
    assert "829.8" in res1["fact"] or "829.8" in res1["plain_summary"]

    # Query 2: Russian Crude Pivot
    q2 = RESEARCH_QUESTIONS_CATALOG[1]
    res2 = assistant.query(q2, mock_stats)
    assert "Russia" in res2["fact"]
    assert "Urals" in res2["interpretation"]

    # Query 3: Mobile PLI Miracle
    q3 = RESEARCH_QUESTIONS_CATALOG[2]
    res3 = assistant.query(q3, mock_stats)
    assert "Electronic goods" in res3["fact"] or "PLI" in res3["plain_summary"]

    # Query 4: Provisional FY 2024-25 Q1 Trajectory
    q7 = RESEARCH_QUESTIONS_CATALOG[6]
    res7 = assistant.query(q7, mock_stats)
    assert "Quarter 1" in res7["plain_summary"] or "April–July" in res7["plain_summary"]
    assert "interim" in res7["interpretation"].lower() or "freight" in res7["interpretation"].lower()
