'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';
const PENDING_3DS_REF_KEY = 'kalai_pending_3ds_reference';
const REFRESH_SECONDS = 30;

type StatusState = 'idle' | 'checking' | 'approved' | 'pending' | 'failed' | 'no-reference';

interface GatewayResult {
  success?: boolean;
  pending?: boolean;
  message?: string;
  merchant_reference?: string;
  result_code?: string;
}

export default function PaymentStatusPage() {
  const [status, setStatus] = useState<StatusState>('idle');
  const [message, setMessage] = useState('Preparing payment verification...');
  const [merchantReference, setMerchantReference] = useState('');
  const [countdown, setCountdown] = useState(0);

  const effectiveReference = useMemo(() => {
    if (merchantReference) {
      return merchantReference;
    }
    if (typeof window === 'undefined') {
      return '';
    }
    return window.sessionStorage.getItem(PENDING_3DS_REF_KEY) ?? '';
  }, [merchantReference]);

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
      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/complete/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ merchant_reference: reference }),
      });

      const result = (await response.json()) as GatewayResult;

      if (result.success && !result.pending) {
        setStatus('approved');
        setMessage(result.message || `Payment approved. Reference: ${result.merchant_reference || reference}`);
        window.sessionStorage.removeItem(PENDING_3DS_REF_KEY);
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
  }, [effectiveReference]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const ref = window.sessionStorage.getItem(PENDING_3DS_REF_KEY) ?? '';
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMerchantReference(ref);
  }, []);

  useEffect(() => {
    if (!merchantReference) {
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void verifyPayment();
  }, [merchantReference, verifyPayment]);

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

  return (
    <main className="min-h-screen bg-linear-to-b from-[#001a33] via-[#002b4d] to-[#001a33] py-16 px-6">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-2xl p-8 md:p-10">
        <div className="flex items-center justify-between gap-3 mb-6">
          <h1 className="text-2xl md:text-3xl font-black text-gray-900">Card Payment Status</h1>
          <span className={`px-3 py-1 rounded-full border text-xs font-bold ${statusBadge}`}>
            {statusLabel}
          </span>
        </div>

        <p className="text-gray-700 leading-relaxed mb-4">{message}</p>

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
      </div>
    </main>
  );
}
