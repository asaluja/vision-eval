"""Shared constants for chart generators."""

from __future__ import annotations

import matplotlib

COLORS = list(matplotlib.cm.tab10.colors[:10])

CATEGORY_POOLS = [
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    ["Product A", "Product B", "Product C", "Product D",
     "Product E", "Product F", "Product G", "Product H"],
    ["North", "South", "East", "West", "Central", "Coastal", "Mountain", "Valley"],
    ["Sales", "Marketing", "Engineering", "Support", "HR", "Finance", "Legal", "Operations"],
]
