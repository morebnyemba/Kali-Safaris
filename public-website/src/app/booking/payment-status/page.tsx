'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { clearCheckoutSession, loadCheckoutSession, retryPaymentHref, type CheckoutPaymentMode } from '@/lib/checkoutSession';
import type { ReactNode } from 'react';
import { FaCheck, FaClock, FaLock, FaRegCopy, FaSearch, FaTimes, FaWhatsapp } from 'react-icons/fa';

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';
const PENDING_3DS_REF_KEY = 'kalai_pending_3ds_reference';
const PENDING_PAYMENT_CHANNEL_KEY = 'kalai_pending_payment_channel';
const PENDING_BOOKING_REFERENCE_KEY = 'kalai_pending_booking_reference';
const RETURN_TO_WHATSAPP_KEY = 'kalai_return_to_whatsapp';
const WHATSAPP_NUMBER = '263712629336';
const REFRESH_SECONDS = 30;

// Terminal failures the backend redirects here with ?error=... — these should
// be shown as-is, never re-verified (re-verifying a failed 3DS just queries a
// DECLINED transaction and hides the real reason).
const HARD_FAILURE_ERRORS = new Set([
  '3ds_failed',
  'not_found',
  'card_data_missing',
  'session_expired',
  'internal',
]);

function describeError(errorCode: string, resultDescription: string): string {
  const detail = resultDescription.trim();
  switch (errorCode) {
    case '3ds_failed':
      return detail
        ? `3D Secure authentication didn't complete: ${detail}. Please try the payment again.`
        : "3D Secure authentication didn't complete. Please try the payment again.";
    case 'session_expired':
      return 'Your secure payment session expired. Please start the payment again.';
    case 'card_data_missing':
      return 'We lost your card session before the charge could be completed. Please try again.';
    case 'not_found':
      return 'We could not find this payment. Please start a new booking payment.';
    default:
      return detail
        ? `The payment could not be completed: ${detail}. Please try again.`
        : 'The payment could not be completed. Please try again.';
  }
}

type PaymentChannel = 'card' | 'ecocash';
type CardProvider = 'copyandpay' | 'cbz';

type StatusState = 'idle' | 'checking' | 'approved' | 'pending' | 'failed' | 'no-reference';

interface GatewayResult {
  success?: boolean;
  pending?: boolean;
  message?: string;
  extended_description?: string;
  merchant_reference?: string;
  booking_reference?: string;
  result_code?: string;
  gateway_mode?: string;
}

const noopSubscribe = () => () => {};
/** Href back to the saved booking's payment step (client-only; '/booking' during SSR). */
function useRetryPaymentHref(mode?: CheckoutPaymentMode) {
  return useSyncExternalStore(noopSubscribe, () => retryPaymentHref(loadCheckoutSession(), mode), () => '/booking');
}

function PaymentStatusPageContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<StatusState>('idle');
  const [message, setMessage] = useState('Getting your payment details…');
  const [detail, setDetail] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [bookingReference, setBookingReference] = useState('');
  const [gatewayMode, setGatewayMode] = useState('');

  const channel = useMemo<PaymentChannel>(() => {
    const queryChannel = (searchParams.get('channel') ?? '').toLowerCase();
    if (queryChannel === 'ecocash' || queryChannel === 'card') {
      return queryChannel as PaymentChannel;
    }
    if (typeof window === 'undefined') {
      return 'card';
    }
    const storedChannel = (window.sessionStorage.getItem(PENDING_PAYMENT_CHANNEL_KEY) ?? '').toLowerCase();
    if (storedChannel === 'ecocash' || storedChannel === 'card') {
      return storedChannel as PaymentChannel;
    }
    return 'card';
  }, [searchParams]);

  const cardProvider = useMemo<CardProvider>(() => {
    const provider = (searchParams.get('provider') ?? '').toLowerCase();
    if (provider === 'copyandpay') {
      return 'copyandpay';
    }
    return 'cbz';
  }, [searchParams]);

  const resourcePath = useMemo(() => searchParams.get('resourcePath') ?? '', [searchParams]);

  // PaRes from the ACS callback (set by /api/3ds/callback route handler after ACS redirect)
  const paRes = useMemo(() => searchParams.get('pares') ?? '', [searchParams]);

  // Terminal error forwarded by the backend (e.g. ?error=3ds_failed&result_description=...)
  const errorCode = useMemo(() => (searchParams.get('error') ?? '').toLowerCase(), [searchParams]);
  const resultDescription = useMemo(() => searchParams.get('result_description') ?? '', [searchParams]);
  const isHardFailure = useMemo(() => HARD_FAILURE_ERRORS.has(errorCode), [errorCode]);

  const effectiveReference = useMemo(() => {
    const queryRef = searchParams.get('ref') ?? '';
    if (queryRef) {
      return queryRef;
    }
    if (typeof window === 'undefined') {
      return '';
    }
    return window.sessionStorage.getItem(PENDING_3DS_REF_KEY) ?? '';
  }, [searchParams]);

  const shouldReturnToWhatsApp = useMemo(() => {
    const querySource = (searchParams.get('source') ?? '').toLowerCase();
    if (querySource === 'whatsapp') {
      return true;
    }
    if (typeof window === 'undefined') {
      return false;
    }
    return window.sessionStorage.getItem(RETURN_TO_WHATSAPP_KEY) === '1';
  }, [searchParams]);

  useEffect(() => {
    const id = window.setTimeout(() => {
      const queryBookingReference = searchParams.get('booking_reference') ?? '';
      if (queryBookingReference) {
        setBookingReference(queryBookingReference);
        return;
      }
      const storedBookingReference = window.sessionStorage.getItem(PENDING_BOOKING_REFERENCE_KEY) ?? '';
      if (storedBookingReference) {
        setBookingReference(storedBookingReference);
      }
    }, 0);

    return () => window.clearTimeout(id);
  }, [searchParams]);

  const verifyPayment = useCallback(async () => {
    const reference = effectiveReference;
    if (!resourcePath && !reference) {
      setStatus('no-reference');
      setMessage('We couldn’t find a payment from this browser. If you were charged, contact us with your booking reference.');
      return;
    }

    setStatus('checking');
    setMessage('We’re confirming the result with the bank. This usually takes a few seconds.');

    try {
      const response = channel === 'card'
        ? resourcePath
          ? await fetch(
              `${API_BASE}/crm-api/payments/cbz/copyandpay/status/?resourcePath=${encodeURIComponent(resourcePath)}${reference ? `&merchant_reference=${encodeURIComponent(reference)}` : ''}`,
              {
                cache: 'no-store',
              },
            )
          : await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/complete/`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                merchant_reference: reference,
                // Forward PaRes from ACS to backend for 3DS completion
                ...(paRes ? { pares: paRes } : {}),
              }),
            })
        : await fetch(`${API_BASE}/crm-api/payments/cbz/query/${reference}/`);

      const result = (await response.json()) as GatewayResult;
      setGatewayMode(result.gateway_mode ?? '');
      setDetail((result.extended_description ?? '').trim());
      if (result.booking_reference) {
        setBookingReference(result.booking_reference);
        window.sessionStorage.setItem(PENDING_BOOKING_REFERENCE_KEY, result.booking_reference);
      }

      if (channel === 'ecocash') {
        if (result.success && (result as GatewayResult & { is_approved?: boolean }).is_approved) {
          setStatus('approved');
          setMessage(
            result.gateway_mode === 'Test'
              ? `Sandbox approval only. iVeri is in Test mode, so no real customer charge was made. Reference: ${reference}`
              : (result.message || `Payment approved. Reference: ${reference}`)
          );
          window.sessionStorage.removeItem(PENDING_3DS_REF_KEY);
          window.sessionStorage.removeItem(PENDING_PAYMENT_CHANNEL_KEY);
          return;
        }

        if (result.success && (result as GatewayResult & { is_pending?: boolean }).is_pending) {
          setStatus('pending');
          setCountdown(REFRESH_SECONDS);
          setMessage(result.message || 'Payment is still pending final confirmation.');
          return;
        }

        setStatus('failed');
        setMessage(result.message || 'Payment could not be confirmed.');
        return;
      }

      if (result.success && !result.pending) {
        setStatus('approved');
        setMessage(
          result.gateway_mode === 'Test'
            ? `Sandbox approval only. ${cardProvider === 'copyandpay' ? 'ZimSwitch' : 'iVeri'} is in Test mode, so no real customer charge was made. Reference: ${result.merchant_reference || reference}`
            : (result.message || `Payment approved. Reference: ${result.merchant_reference || reference}`)
        );
        window.sessionStorage.removeItem(PENDING_3DS_REF_KEY);
        window.sessionStorage.removeItem(PENDING_PAYMENT_CHANNEL_KEY);
        return;
      }

      if (result.pending) {
        setStatus('pending');
        setCountdown(REFRESH_SECONDS);
        setMessage(result.message || 'Payment is still pending final confirmation.');
        return;
      }

      setStatus('failed');
      setMessage(result.message || 'Payment could not be confirmed.');
    } catch {
      setStatus('failed');
      setMessage('Unable to reach payment services right now. Please try again.');
    }
  }, [cardProvider, channel, effectiveReference, paRes, resourcePath]);

  // Backend signalled a terminal failure — show it, don't re-verify.
  // Defer the setState out of the effect body to satisfy react-hooks lint.
  useEffect(() => {
    if (!isHardFailure) {
      return;
    }
    const id = window.setTimeout(() => {
      setStatus('failed');
      setMessage(describeError(errorCode, resultDescription));
    }, 0);
    return () => window.clearTimeout(id);
  }, [isHardFailure, errorCode, resultDescription]);

  useEffect(() => {
    if (isHardFailure) {
      return;
    }
    if (!effectiveReference && !resourcePath) {
      return;
    }
    const id = window.setTimeout(() => {
      void verifyPayment();
    }, 0);
    return () => window.clearTimeout(id);
  }, [isHardFailure, effectiveReference, resourcePath, verifyPayment]);

  useEffect(() => {
    if (status !== 'pending') {
      return;
    }
    // Only mutate state from inside the interval callback (never the effect body)
    // so the lint rule is satisfied. First tick resets counter to REFRESH_SECONDS.
    const id = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          void verifyPayment();
          return REFRESH_SECONDS;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [status, verifyPayment]);

  const returnToWhatsAppHref = useMemo(() => {
    if (!shouldReturnToWhatsApp) {
      return '';
    }
    const parts = [
      'Hi Kalai Safaris, I have completed my website card payment.',
      bookingReference ? `Booking reference: ${bookingReference}.` : '',
      effectiveReference ? `Merchant reference: ${effectiveReference}.` : '',
      'Please continue with my WhatsApp booking.',
    ].filter(Boolean);

    return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(parts.join(' '))}`;
  }, [bookingReference, effectiveReference, shouldReturnToWhatsApp]);

  const helpHref = useMemo(() => {
    const text = [
      'Hi Kalai Safaris, I need help with a payment on your website.',
      bookingReference ? `Booking reference: ${bookingReference}.` : '',
      effectiveReference ? `Payment reference: ${effectiveReference}.` : '',
    ].filter(Boolean).join(' ');
    return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`;
  }, [bookingReference, effectiveReference]);

  const retryHref = useRetryPaymentHref(channel === 'ecocash' ? 'ecocash' : 'card');
  // Paid — nothing left to retry.
  useEffect(() => {
    if (status === 'approved') clearCheckoutSession();
  }, [status]);

  const view = STATE_VIEW[status];
  const methodLabel = channel === 'ecocash'
    ? 'EcoCash'
    : cardProvider === 'copyandpay' ? 'ZimSwitch card' : 'Visa / Mastercard';
  const isTest = gatewayMode === 'Test';

  return (
    <main className="min-h-[calc(100vh-3.5rem)] bg-[#FFF9F5] px-4 py-10 sm:py-16">
      <div className="mx-auto w-full max-w-lg">
        <section className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-[0_20px_50px_-30px_rgba(0,0,0,0.35)]" aria-live="polite">
          <div className={`relative px-6 pb-6 pt-10 text-center sm:px-10 ${view.band}`}>
            <span className={`mx-auto mb-5 flex size-20 items-center justify-center rounded-full ring-8 ${view.icon}`}>
              {view.glyph}
            </span>
            <h1 className="text-2xl font-black tracking-tight text-gray-900 sm:text-3xl">{view.title}</h1>
            <p className="mx-auto mt-2 max-w-sm text-[15px] leading-relaxed text-gray-600">
              {status === 'approved' ? view.lead : message}
            </p>
            {isTest && (
              <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-amber-800">
                Test mode · no real money moved
              </span>
            )}
          </div>

          {status === 'pending' && (
            <div className="h-1 w-full bg-amber-100" role="progressbar" aria-label="Time until the next automatic check" aria-valuemin={0} aria-valuemax={REFRESH_SECONDS} aria-valuenow={countdown}>
              <div className="h-1 bg-amber-500 transition-[width] duration-1000 ease-linear" style={{ width: `${countdown ? ((REFRESH_SECONDS - countdown) / REFRESH_SECONDS) * 100 : 0}%` }} />
            </div>
          )}

          <div className="space-y-6 px-6 py-6 sm:px-10">
            {detail && status !== 'approved' && (
              <p className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-600">{detail}</p>
            )}
            {status === 'approved' && message && !message.startsWith('Sandbox') && message !== view.lead && (
              <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{message}</p>
            )}

            {(bookingReference || effectiveReference || status !== 'no-reference') && (
              <dl className="divide-y divide-gray-100 rounded-2xl border border-gray-100 text-sm">
                {bookingReference && <DetailRow label="Booking reference" value={bookingReference} copy />}
                {effectiveReference && <DetailRow label="Payment reference" value={effectiveReference} copy />}
                <DetailRow label="Payment method" value={methodLabel} />
                {status === 'pending' && countdown > 0 && <DetailRow label="Next automatic check" value={`in ${countdown}s`} />}
              </dl>
            )}

            {returnToWhatsAppHref && status === 'approved' && (
              <a href={returnToWhatsAppHref} target="_blank" rel="noreferrer"
                className="flex items-center justify-center gap-2 rounded-full bg-[#25D366] px-5 py-3.5 font-bold text-white shadow-sm transition hover:bg-[#1EBE5A]">
                <FaWhatsapp size={20} aria-hidden /> Continue on WhatsApp
              </a>
            )}

            <div className="flex flex-col gap-3 sm:flex-row">
              {status === 'approved' ? (
                <>
                  <Link href="/" className="flex-1 rounded-full bg-[#C8102E] px-5 py-3 text-center font-bold text-white transition hover:bg-[#A00D24]">Back to home</Link>
                  <Link href="/booking" className="flex-1 rounded-full border border-gray-300 px-5 py-3 text-center font-semibold text-gray-700 transition hover:bg-gray-50">Book another cruise</Link>
                </>
              ) : status === 'no-reference' ? (
                <Link href="/booking" className="flex-1 rounded-full bg-[#C8102E] px-5 py-3 text-center font-bold text-white transition hover:bg-[#A00D24]">Book a cruise</Link>
              ) : (
                <>
                  {isHardFailure || status === 'failed' ? (
                    <Link href={retryHref} className="flex-1 rounded-full bg-[#C8102E] px-5 py-3 text-center font-bold text-white transition hover:bg-[#A00D24]">{retryHref === '/booking' ? 'Start a new booking' : 'Try the payment again'}</Link>
                  ) : null}
                  {!isHardFailure && (
                    <button type="button" onClick={() => void verifyPayment()} disabled={status === 'checking'}
                      className={`flex-1 rounded-full px-5 py-3 font-semibold transition disabled:opacity-60 ${status === 'failed' ? 'border border-gray-300 text-gray-700 hover:bg-gray-50' : 'bg-[#C8102E] font-bold text-white hover:bg-[#A00D24]'}`}>
                      {status === 'checking' ? 'Checking…' : 'Check again now'}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-gray-100 bg-gray-50/70 px-6 py-4 text-xs text-gray-500 sm:px-10">
            <span className="flex items-center gap-1.5"><FaLock className="text-emerald-600" aria-hidden /> Verified directly with the bank</span>
            <a href={helpHref} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 font-semibold text-gray-700 hover:text-[#128C7E]">
              <FaWhatsapp className="text-[#25D366]" aria-hidden /> Need help?
            </a>
          </div>
        </section>

        {status === 'approved' && (
          <p className="mt-5 text-center text-xs text-gray-500">Keep your booking reference handy in case you need to contact us.</p>
        )}
      </div>
    </main>
  );
}

function DetailRow({ label, value, copy = false }: { label: string; value: string; copy?: boolean }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-3">
      <dt className="shrink-0 text-gray-500">{label}</dt>
      <dd className="flex min-w-0 items-center gap-2 font-semibold text-gray-900">
        <span className={`truncate ${copy ? 'font-mono text-[13px]' : ''}`}>{value}</span>
        {copy && (
          <button
            type="button"
            onClick={() => {
              navigator.clipboard?.writeText(value).then(() => {
                setCopied(true);
                window.setTimeout(() => setCopied(false), 1500);
              }).catch(() => {});
            }}
            className="shrink-0 rounded-md p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
            aria-label={`Copy ${label.toLowerCase()}`}
          >
            {copied ? <FaCheck className="text-emerald-600" size={12} /> : <FaRegCopy size={12} />}
          </button>
        )}
      </dd>
    </div>
  );
}

const spinner = <span className="size-9 animate-spin rounded-full border-4 border-current border-t-transparent" aria-hidden />;

const STATE_VIEW: Record<StatusState, { title: string; lead: string; band: string; icon: string; glyph: ReactNode }> = {
  approved: {
    title: 'Payment confirmed',
    lead: 'Thank you — we’ve received your payment.',
    band: 'bg-gradient-to-b from-emerald-50 to-white',
    icon: 'bg-emerald-500 text-white ring-emerald-100',
    glyph: <FaCheck size={34} aria-hidden />,
  },
  pending: {
    title: 'Waiting for the bank',
    lead: '',
    band: 'bg-gradient-to-b from-amber-50 to-white',
    icon: 'bg-amber-400 text-white ring-amber-100',
    glyph: <FaClock size={32} aria-hidden />,
  },
  failed: {
    title: 'Payment not completed',
    lead: '',
    band: 'bg-gradient-to-b from-red-50 to-white',
    icon: 'bg-[#C8102E] text-white ring-red-100',
    glyph: <FaTimes size={32} aria-hidden />,
  },
  checking: {
    title: 'Checking your payment…',
    lead: '',
    band: 'bg-gradient-to-b from-orange-50 to-white',
    icon: 'bg-white text-[#E8600A] ring-orange-100',
    glyph: spinner,
  },
  idle: {
    title: 'One moment…',
    lead: '',
    band: 'bg-gradient-to-b from-orange-50 to-white',
    icon: 'bg-white text-[#E8600A] ring-orange-100',
    glyph: spinner,
  },
  'no-reference': {
    title: 'No payment to check',
    lead: '',
    band: 'bg-gradient-to-b from-gray-50 to-white',
    icon: 'bg-gray-200 text-gray-500 ring-gray-100',
    glyph: <FaSearch size={28} aria-hidden />,
  },
};

export default function PaymentStatusPage() {
  return (
    <Suspense fallback={null}>
      <PaymentStatusPageContent />
    </Suspense>
  );
}
