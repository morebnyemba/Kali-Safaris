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

type PaymentChannel = 'card' | 'ecocash';

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
    if (!reference) {
      setStatus('no-reference');
      setMessage('No pending 3DS payment was found.');
      return;
    }

    setStatus('checking');
    setMessage('Checking your payment status with the gateway...');

    try {
      const response = channel === 'card'
        ? await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/complete/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ merchant_reference: reference }),
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
            ? `Sandbox approval only. iVeri is in Test mode, so no real customer charge was made. Reference: ${result.merchant_reference || reference}`
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
  }, [effectiveReference, channel]);

  useEffect(() => {
    if (!effectiveReference) {
      return;
    }
    const id = window.setTimeout(() => {
      void verifyPayment();
    }, 0);
    return () => window.clearTimeout(id);
  }, [effectiveReference, verifyPayment]);

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
            This transaction was processed against the iVeri sandbox. Use a LIVE application ID and `CBZ_MODE=LIVE` before treating approvals as real payments.
          </div>
        )}

        <p className="text-sm text-gray-500 mb-2">
          Channel: <span className="font-semibold text-gray-700 uppercase">{channel}</span>
        </p>

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
          <button
            type="button"
            onClick={() => void verifyPayment()}
            disabled={status === 'checking'}
            className="rounded-full bg-linear-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black font-bold py-3 px-5 transition-all disabled:opacity-60"
          >
            {status === 'checking' ? 'Checking...' : 'Check Again'}
          </button>
          <Link
            href="/booking"
            className="rounded-full border border-gray-300 text-gray-700 font-semibold py-3 px-5 text-center hover:bg-gray-50 transition"
          >
            Back to Booking
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
