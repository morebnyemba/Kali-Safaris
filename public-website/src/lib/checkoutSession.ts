// Remembers the in-progress checkout for this browser tab so a failed or cancelled
// payment can be retried from the payment step instead of re-entering every detail.
//
// Only references are stored — the passenger details and ID documents already live
// server-side on the draft booking created by the first payment attempt. Personal
// data is deliberately NOT kept in browser storage.

const KEY = 'kalai_checkout_session';
const MAX_AGE_MS = 24 * 60 * 60 * 1000;

export type CheckoutPaymentMode = 'card' | 'ecocash' | 'omari';

export interface CheckoutSession {
  bookingReference: string;
  amount: number;
  tourName: string;
  paymentMode: CheckoutPaymentMode;
  fromWhatsApp: boolean;
  savedAt: number;
}

export function saveCheckoutSession(session: Omit<CheckoutSession, 'savedAt'>) {
  if (!session.bookingReference || !(session.amount > 0)) return;
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify({ ...session, savedAt: Date.now() }));
  } catch {
    // Storage blocked (private mode etc.) — retry just falls back to a fresh booking.
  }
}

export function loadCheckoutSession(): CheckoutSession | null {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as CheckoutSession;
    if (!session.bookingReference || Date.now() - session.savedAt > MAX_AGE_MS) {
      window.sessionStorage.removeItem(KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function clearCheckoutSession() {
  try {
    window.sessionStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}

/** Link back to the payment step of the saved booking, or the start of booking if none. */
export function retryPaymentHref(session: CheckoutSession | null, paymentMode?: CheckoutPaymentMode): string {
  if (!session) return '/booking';
  const params = new URLSearchParams({
    booking_reference: session.bookingReference,
    amount: session.amount.toFixed(2),
    tour_name: session.tourName,
    payment_mode: paymentMode || session.paymentMode,
  });
  if (session.fromWhatsApp) params.set('source', 'whatsapp');
  return `/booking?${params.toString()}`;
}
