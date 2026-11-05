// Mirrors whatsappcrm_backend/customer_data/payment_plan.py (a backend test keeps these equal).
// The server is the authority: it re-checks the date and the deposit amount at payment.
export const INSTALMENT_MIN_DAYS_AHEAD = 30;
export const DEPOSIT_PERCENT = 50;
export const BALANCE_DUE_DAYS_BEFORE = 14;

export type PaymentPlan = 'full' | 'deposit';

const DAY_MS = 86_400_000;

const toUtc = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return Date.UTC(y, (m || 1) - 1, d || 1);
};

/** Whole days from `todayIso` to `dateIso` (both YYYY-MM-DD, Victoria Falls dates). */
export const daysAhead = (dateIso: string, todayIso: string) => Math.round((toUtc(dateIso) - toUtc(todayIso)) / DAY_MS);

export const instalmentsAllowed = (dateIso: string, todayIso: string) =>
  Boolean(dateIso) && daysAhead(dateIso, todayIso) > INSTALMENT_MIN_DAYS_AHEAD;

/** Deposit rounded half-up to the cent, like the server. */
export const depositAmount = (total: number) => Math.round(total * DEPOSIT_PERCENT + 1e-6) / 100;

export const balanceDueDate = (dateIso: string) =>
  new Date(toUtc(dateIso) - BALANCE_DUE_DAYS_BEFORE * DAY_MS)
    .toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
