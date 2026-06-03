"""Bridge to the bundled or user-configured legacy Bazi scripts.

GitHub users can run with the bundled ``bazi_legacy`` folder.  Local developers
may still point ``BAZI_ENGINE_DIR`` at another legacy engine directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .calendar_terms import apply_to_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE_DIR = PROJECT_ROOT / "bazi_legacy"
ENGINE_DIR = Path(os.environ.get("BAZI_ENGINE_DIR", str(DEFAULT_ENGINE_DIR)))


def ensure_engine_path() -> Path:
    """Add the configured engine directory to ``sys.path`` and return it."""

    if not ENGINE_DIR.exists():
        raise RuntimeError(
            f"Bazi engine directory not found: {ENGINE_DIR}. "
            "Set BAZI_ENGINE_DIR to the folder containing bazi_engine.py."
        )
    engine_path = str(ENGINE_DIR)
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    return ENGINE_DIR


def load_core() -> dict[str, Any]:
    """Import and return the existing core engine classes/functions."""

    ensure_engine_path()
    import bazi_engine  # type: ignore
    from bazi_engine import BaziChart  # type: ignore
    from narrator import NarratorEngine  # type: ignore

    apply_to_module(bazi_engine)
    return {
        "BaziChart": BaziChart,
        "NarratorEngine": NarratorEngine,
    }
