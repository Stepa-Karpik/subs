export function formatMoney(value?: number | null, estimated = false) {
  if (value === null || value === undefined) return '—';
  const rub = value / 100;
  const formatted = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(rub) + ' ₽';
  return estimated ? `≈ ${formatted}` : formatted;
}

export function toMinor(rubles: string | number) {
  const value = typeof rubles === 'number' ? rubles : Number(String(rubles).replace(',', '.'));
  if (!Number.isFinite(value)) return 0;
  return Math.round(value * 100);
}

export function fromMinor(minor?: number | null) {
  if (minor === null || minor === undefined) return '';
  return String(Math.round(minor / 100));
}

const intervalsPerYear: Record<string, number> = { weekly: 52, monthly: 12, semi_annual: 2, annual: 1 };
export function monthlyFromAmount(amountMinor: number, interval: string) { return Math.round((amountMinor * intervalsPerYear[interval]) / 12); }
export function yearlyFromAmount(amountMinor: number, interval: string) { return Math.round(amountMinor * intervalsPerYear[interval]); }
export function amountFromMonthly(monthlyMinor: number, interval: string) { return Math.round((monthlyMinor * 12) / intervalsPerYear[interval]); }
export function amountFromYearly(yearlyMinor: number, interval: string) { return Math.round(yearlyMinor / intervalsPerYear[interval]); }
