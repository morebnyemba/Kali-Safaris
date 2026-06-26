'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';

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
  merchant_reference?: string;
  booking_reference?: string;
  result_code?: string;
  gateway_mode?: string;
}

function PaymentStatusPageContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<StatusState>('idle');
  const [message, setMessage] = useState('Preparing payment verification...');
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
      setMessage('No pending 3DS payment was found.');
      return;
    }

    setStatus('checking');
    setMessage('Checking your payment status with the gateway...');

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
            ? `Sandbox approval only. ${cardProvider === 'copyandpay' ? 'COPYandPAY' : 'iVeri'} is in Test mode, so no real customer charge was made. Reference: ${result.merchant_reference || reference}`
            : (result.message || `Payment approved. Reference: ${result.merchant_reference || reference}`)
        );
        window.sessionStorage.removeItem(PENDING_3DS_REF_KEY);
        window.sessionStorage.removeItem(PENDING_PAYMENT_CHANNEL_KEY);
        return;
      }

      if (result.pending) {
        setStatus('pending');
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

  const statusBadge = {
    approved: 'bg-green-100 text-green-800 border-green-200',
    pending: 'bg-amber-100 text-amber-800 border-amber-200',
    failed: 'bg-red-100 text-red-800 border-red-200',
    checking: 'bg-blue-100 text-blue-800 border-blue-200',
    idle: 'bg-slate-100 text-slate-700 border-slate-200',
    'no-reference': 'bg-slate-100 text-slate-700 border-slate-200',
  }[status];

  const statusLabel = {
    approved: 'Approved',
    pending: 'Pending',
    failed: 'Not Confirmed',
    checking: 'Checking',
    idle: 'Preparing',
    'no-reference': 'No Reference',
  }[status];

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

  return (
    <main className="min-h-screen bg-linear-to-b from-[#001a33] via-[#002b4d] to-[#001a33] py-16 px-6">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-2xl p-8 md:p-10">
        <div className="flex items-center justify-between gap-3 mb-6">
            <h1 className="text-2xl md:text-3xl font-black text-gray-900">{channel === 'ecocash' ? 'EcoCash Payment Status' : 'Card Payment Status'}</h1>
          <span className={`px-3 py-1 rounded-full border text-xs font-bold ${statusBadge}`}>
            {statusLabel}
          </span>
        </div>

        <p className="text-gray-700 leading-relaxed mb-4">{message}</p>

        {gatewayMode === 'Test' && (
          <div className="mb-4 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            This transaction was processed against the {cardProvider === 'copyandpay' ? 'COPYandPAY' : 'iVeri'} sandbox. Use live gateway credentials before treating approvals as real payments.
          </div>
        )}

        <p className="text-sm text-gray-500 mb-2">
          Channel: <span className="font-semibold text-gray-700 uppercase">{channel}</span>
        </p>

        {channel === 'card' && (
          <p className="text-sm text-gray-500 mb-2">
            Provider: <span className="font-semibold text-gray-700 uppercase">{cardProvider}</span>
          </p>
        )}

        {status === 'pending' && countdown > 0 && (
          <p className="text-sm text-amber-700 mb-2">
            Rechecking automatically in{' '}
            <span className="font-bold">{countdown}s</span>
          </p>
        )}

        {effectiveReference && (
          <p className="text-sm text-gray-500 mb-8">
            Merchant reference: <span className="font-semibold text-gray-700">{effectiveReference}</span>
          </p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {!isHardFailure && (
            <button
              type="button"
              onClick={() => void verifyPayment()}
              disabled={status === 'checking'}
              className="rounded-full bg-linear-to-r from-[#E09A18] to-[#E8600A] hover:from-[#E8600A] hover:to-[#F47B1A] text-black font-bold py-3 px-5 transition-all disabled:opacity-60"
            >
              {status === 'checking' ? 'Checking...' : 'Check Again'}
            </button>
          )}
          <Link
            href="/booking"
            className="rounded-full border border-gray-300 text-gray-700 font-semibold py-3 px-5 text-center hover:bg-gray-50 transition"
          >
            {isHardFailure ? 'Try Payment Again' : 'Back to Booking'}
          </Link>
        </div>

        {returnToWhatsAppHref && (
          <a
            href={returnToWhatsAppHref}
            target="_blank"
            rel="noreferrer"
            className="mt-3 block rounded-full border border-green-500 bg-green-50 px-5 py-3 text-center font-semibold text-green-700 transition hover:bg-green-100"
          >
            Return to WhatsApp
          </a>
        )}
      </div>
    </main>
  );
}

export default function PaymentStatusPage() {
  return (
    <Suspense fallback={null}>
      <PaymentStatusPageContent />
    </Suspense>
  );
}
