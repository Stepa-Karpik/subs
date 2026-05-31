from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

INTERVALS_PER_YEAR = {
    "weekly": Decimal("52"),
    "monthly": Decimal("12"),
    "semi_annual": Decimal("2"),
    "annual": Decimal("1"),
}


@dataclass(frozen=True)
class NormalizedAmount:
    interval_amount_minor: int | None
    monthly_minor: int | None
    yearly_minor: int | None
    is_estimated: bool


def _round_minor(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def normalize_amount(amount_minor: int | None, billing_interval: str, amount_model: str = "fixed") -> NormalizedAmount:
    if amount_model == "unknown" or amount_minor is None:
        return NormalizedAmount(None, None, None, amount_model in {"variable", "custom"})
    if amount_model == "free":
        return NormalizedAmount(0, 0, 0, False)
    intervals = INTERVALS_PER_YEAR[billing_interval]
    yearly = _round_minor(Decimal(amount_minor) * intervals)
    monthly = _round_minor(Decimal(yearly) / Decimal("12"))
    return NormalizedAmount(amount_minor, monthly, yearly, amount_model in {"variable", "custom"})


def amount_from_monthly(monthly_minor: int, billing_interval: str) -> int:
    yearly = Decimal(monthly_minor) * Decimal("12")
    return _round_minor(yearly / INTERVALS_PER_YEAR[billing_interval])


def amount_from_yearly(yearly_minor: int, billing_interval: str) -> int:
    return _round_minor(Decimal(yearly_minor) / INTERVALS_PER_YEAR[billing_interval])


def add_months(value: date, months: int) -> date:
    target_month = value.month - 1 + months
    year = value.year + target_month // 12
    month = target_month % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def next_occurrence_dates(anchor: date, billing_interval: str, months_ahead: int = 12, today: date | None = None) -> list[date]:
    today = today or date.today()
    if billing_interval == "weekly":
        step_days = 7
        current = anchor
        while current < today:
            current = date.fromordinal(current.toordinal() + step_days)
        end = add_months(today, months_ahead)
        out = []
        while current < end:
            out.append(current)
            current = date.fromordinal(current.toordinal() + step_days)
        return out

    step_months = {"monthly": 1, "semi_annual": 6, "annual": 12}[billing_interval]
    current = anchor
    while current < today:
        current = add_months(current, step_months)
    end = add_months(today, months_ahead)
    out = []
    while current < end:
        out.append(current)
        current = add_months(current, step_months)
    return out


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"
