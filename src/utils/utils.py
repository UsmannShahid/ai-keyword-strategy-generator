"""
General utility functions.
"""

import re
from datetime import datetime

def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    if not text:
        return ""
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def default_report_name(business_desc: str = "") -> str:
    """Generate a default report name."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if business_desc:
        slug = slugify(business_desc)[:30]
        return f"keywords_{slug}_{timestamp}"
    return f"keywords_report_{timestamp}"