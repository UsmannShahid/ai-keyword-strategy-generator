# ai_keyword_tool/utils.py
import re, datetime as dt

def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "report"

def default_report_name(business: str = "") -> str:
    today = dt.date.today().strftime("%Y-%m-%d")
    base = slugify(business) or "keywords"
    return f"{base}-{today}"
