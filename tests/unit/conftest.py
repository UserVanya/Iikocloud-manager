"""Unit-test isolation: avoid loading heavy iikocloud package __init__.py."""

from __future__ import annotations

import sys
import types
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
_pkg = types.ModuleType("iikocloud")
_pkg.__path__ = [str(_root / "iikocloud")]
sys.modules.setdefault("iikocloud", _pkg)
