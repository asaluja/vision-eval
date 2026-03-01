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

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SERIES_POOLS = [
    ["Revenue", "Cost", "Profit", "Tax", "Margin", "COGS", "Net", "Debt", "Equity", "Dividends"],
    ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    ["Online", "In-Store", "Wholesale", "Direct", "Partner", "Reseller", "OEM", "Retail", "B2B", "Export"],
]
