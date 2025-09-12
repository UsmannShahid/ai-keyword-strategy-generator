"""
Free API entrypoint.

This module exposes a FastAPI `app` for the Free version. It first tries to
import a local implementation `ai-keyword-tool.api-free.app`. If not present,
it falls back to loading the existing implementation under
`free-version/api/main_serp_simple.py` to avoid breakage during migration.

Run locally:
    uvicorn ai-keyword-tool.api-free.main:app --port 8003 --reload
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType


def _load_free_api() -> ModuleType:
    here = pathlib.Path(__file__).resolve()
    # Locate ../../free-version/api/main_serp_simple.py (sibling to ai-keyword-tool)
    candidate = (here.parent.parent.parent / "free-version" / "api" / "main_serp_simple.py").resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Free API implementation not found at: {candidate}")
    spec = importlib.util.spec_from_file_location("free_api", str(candidate))
    if spec is None or spec.loader is None:
        raise ImportError("Could not create import spec for free API")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["free_api"] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


# Prefer local implementation if present
try:
    from .app import app as app  # type: ignore
except Exception:
    _impl = _load_free_api()
    app = getattr(_impl, "app", None)
if app is None:
    raise AttributeError("Expected `app` in free API module but none found")


if __name__ == "__main__":
    # Convenience local runner
    try:
        import uvicorn  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit("uvicorn is required to run the server: pip install uvicorn") from e
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
