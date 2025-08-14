# tests/test_scoring.py
import pandas as pd
from scoring import is_long_tail, has_modifier, guess_competition_score, opportunity_from_row, add_scores

def test_long_tail_and_modifiers():
    assert is_long_tail("best email marketing tools")
    assert has_modifier("pricing for crm software")
    assert not has_modifier("email marketing")

def test_competition_bounds():
    for kw in ["crm", "crm pricing", "best crm software for startups"]:
        c = guess_competition_score(kw)
        assert 0 <= c <= 100

def test_opportunity_increases_with_intent_and_specificity():
    base = opportunity_from_row("email marketing", "informational")
    better = opportunity_from_row("best email marketing tools pricing", "transactional")
    assert better > base

def test_add_scores_produces_columns_and_priority_order():
    df = pd.DataFrame({
        "keyword": ["crm", "crm pricing", "best crm for startups"],
        "category": ["informational", "transactional", "transactional"]
    })
    out = add_scores(df)
    assert {"opportunity", "priority"}.issubset(out.columns)
    # Priority 1 should be the highest opportunity
    top = out.sort_values("priority").iloc[0]
    assert top["opportunity"] == out["opportunity"].max()
