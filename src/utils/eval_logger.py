"""
Evaluation logging utilities.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

def log_eval(data: Dict[str, Any], log_path: str = "data/evals.jsonl") -> None:
    """Log evaluation data to JSONL file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Add timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Append to JSONL file
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"Warning: Could not log eval data: {e}")