import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns';

const toDate = (value) => {
  if (!value) return null;
  const date = value instanceof Date ? value : parseISO(String(value));
  return isValid(date) ? date : null;
};

export const formatMoney = (value, currency = 'USD') => {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return '—';
  return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount);
};

export const formatNumber = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? new Intl.NumberFormat().format(n) : '—';
};

export const formatDate = (value, pattern = 'd MMM yyyy') => {
  const date = toDate(value);
  return date ? format(date, pattern) : '—';
};

export const formatDateTime = (value) => formatDate(value, 'd MMM yyyy, HH:mm');

export const formatRelative = (value) => {
  const date = toDate(value);
  return date ? formatDistanceToNow(date, { addSuffix: true }) : '—';
};

// Local YYYY-MM-DD (toISOString would shift the date across UTC midnight).
export const toIsoDate = (date) => {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

/** Flattens a DRF error payload ({field: [msgs]} / {detail}) into one readable line. */
export const apiErrorMessage = (err, fallback = 'Something went wrong.') => {
  const data = err?.response?.data;
  if (data && typeof data === 'object' && !(data instanceof Blob)) {
    if (typeof data.detail === 'string') return data.detail;
    const parts = Object.entries(data).map(([field, value]) => {
      const text = Array.isArray(value) ? value.join(' ') : typeof value === 'object' ? JSON.stringify(value) : String(value);
      return field === 'non_field_errors' || field === 'error' ? text : `${field.replace(/_/g, ' ')}: ${text}`;
    });
    if (parts.length) return parts.join(' · ');
  }
  return err?.message || fallback;
};
