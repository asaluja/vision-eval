"""Utilities shared across dataset adapters."""

from __future__ import annotations

import re


def parse_bracketed_answer(text: str) -> str:
    """Extract answer from {curly bracket} format used by both benchmarks."""
    match = re.search(r"\{([^}]*)\}", text)
    return match.group(1).strip() if match else text.strip()
