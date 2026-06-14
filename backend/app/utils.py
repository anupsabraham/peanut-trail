from datetime import date, timedelta

from typing import Optional


def compute_trend(data_points: list[Optional[float]], days_in_month: int) -> list[Optional[float]]:
    x_points = []
    y_points = []
    for i, val in enumerate(data_points):
        if val is not None:
            x_points.append(i + 1)
            y_points.append(val)

    n = len(x_points)
    if n > 1:
        sum_x = sum(x_points)
        sum_y = sum(y_points)
        sum_xy = sum(x * y for x, y in zip(x_points, y_points))
        sum_xx = sum(x * x for x in x_points)
        denominator = n * sum_xx - sum_x**2
        if denominator != 0:
            m = (n * sum_xy - sum_x * sum_y) / denominator
            c = (sum_y - m * sum_x) / n
        else:
            m, c = 0, 0
    elif n == 1:
        m = y_points[0] / x_points[0]
        c = 0
    else:
        m, c = 0, 0

    trend = []
    for day in range(1, 32):
        if day <= days_in_month:
            val = m * day + c
            trend.append(float(max(0, val)))
        else:
            trend.append(None)

    return trend

def days_in_month(year: int, month: int) -> int:
    if month == 12:
        return (date(year + 1, 1, 1) - timedelta(days=1)).day
    return (date(year, month + 1, 1) - timedelta(days=1)).day

