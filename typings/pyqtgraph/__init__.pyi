"""Shallow stubs for optional pyqtgraph (USE_GUI). Runtime uses the real package."""
from typing import Any

def __getattr__(name: str) -> Any: ...
