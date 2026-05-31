from datetime import date
from app.services.billing_calculator import amount_from_monthly, amount_from_yearly, next_occurrence_dates, normalize_amount


def test_monthly_price_normalizes_to_yearly():
    result = normalize_amount(100_00, "monthly", "fixed")
    assert result.monthly_minor == 100_00
    assert result.yearly_minor == 1200_00
    assert result.is_estimated is False


def test_yearly_input_converts_to_monthly_interval_amount():
    assert amount_from_yearly(1200_00, "monthly") == 100_00
    assert amount_from_monthly(100_00, "annual") == 1200_00


def test_weekly_price_uses_52_weeks():
    result = normalize_amount(100_00, "weekly", "fixed")
    assert result.yearly_minor == 5200_00
    assert result.monthly_minor == 433_33


def test_month_end_renewal_rolls_to_last_day():
    dates = next_occurrence_dates(date(2026, 1, 31), "monthly", months_ahead=3, today=date(2026, 2, 1))
    assert dates[:3] == [date(2026, 2, 28), date(2026, 3, 28), date(2026, 4, 28)]
