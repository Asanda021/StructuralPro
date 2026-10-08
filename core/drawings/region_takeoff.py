"""Geometry adapters for converting a selected viewport rectangle to takeoff polygon points."""
from __future__ import annotations

import math


def rectangle_to_points(left: float, top: float, right: float, bottom: float) -> tuple[tuple[float, float], ...]:
    """Return a normalized, non-zero rectangle as polygon vertices in scene coordinates."""
    values = tuple(float(v) for v in (left, top, right, bottom))
    if not all(math.isfinite(v) for v in values):
        raise ValueError("مختصات ناحیه باید عددی و متناهی باشند")
    x1, y1, x2, y2 = values
    x_min, x_max = sorted((x1, x2))
    y_min, y_max = sorted((y1, y2))
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("ناحیه انتخاب‌شده باید عرض و ارتفاع مثبت داشته باشد")
    return (
        (x_min, y_min),
        (x_max, y_min),
        (x_max, y_max),
        (x_min, y_max),
    )
