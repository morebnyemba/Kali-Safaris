'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FaCcVisa, FaCcMastercard, FaCcAmex,
  FaLock, FaShieldAlt, FaArrowLeft,
} from 'react-icons/fa';

function CardCheckoutContent() {
  const searchParams = useSearchParams();
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState('');

  const checkoutId = (searchParams.get('checkoutId') || '').trim();
  const merchantReference = (searchParams.get('merchantRef') || '').trim();
  const brands = (searchParams.get('brands') || 'VISA MASTER AMEX ZIMSWITCH').trim();
  const widgetScriptUrl = (searchParams.get('widget') || '').trim();
  const integrity = (searchParams.get('integrity') || '').trim();
  const returnUrl = (searchParams.get('returnUrl') || '/booking/payment-status?channel=card').trim();

  const resolvedScriptUrl = useMemo(() => {
    if (widgetScriptUrl) return widgetScriptUrl;
    if (!checkoutId) return '';
    return `https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId=${encodeURIComponent(checkoutId)}`;
  }, [checkoutId, widgetScriptUrl]);

  useEffect(() => {
    if (!resolvedScriptUrl || !checkoutId) return;

    setScriptLoaded(false);
    setScriptError('');

    const existing = document.querySelector('script[data-copyandpay-widget="1"]');
    if (existing) existing.remove();

    const script = document.createElement('script');
    script.src = resolvedScriptUrl;
    script.async = true;
    script.setAttribute('data-copyandpay-widget', '1');
    script.crossOrigin = 'anonymous';
    if (integrity) script.integrity = integrity;

    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setScriptError('Unable to load secure card widget. Please refresh and try again.');

    document.body.appendChild(script);
    return () => { script.remove(); };
  }, [checkoutId, integrity, resolvedScriptUrl]);

  const errorState = (
    <main className="min-h-screen bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-[#001a33] to-[#003366] px-8 py-6 flex items-center gap-3">
          <FaLock className="text-amber-400 text-xl flex-shrink-0" />
          <span className="text-white font-bold text-lg tracking-tight">Secure Card Checkout</span>
        </div>
        <div className="px-8 py-8">
          <p className="text-gray-600 mb-6">No checkout session found. Please restart the card payment from your booking.</p>
          <Link
            href="/booking"
            className="inline-flex items-center gap-2 rounded-full bg-[#001a33] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#003366]"
          >
            <FaArrowLeft className="text-xs" /> Back to Booking
          </Link>
        </div>
      </div>
    </main>
  );

  if (!checkoutId || !resolvedScriptUrl) return errorState;

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="bg-gradient-to-r from-[#001a33] to-[#003366] px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-400/20">
                <FaLock className="text-amber-400 text-base" />
              </div>
              <div>
                <h1 className="text-white font-bold text-lg leading-tight tracking-tight">Secure Card Checkout</h1>
                <p className="text-blue-200 text-xs mt-0.5">256-bit SSL encrypted</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5">
              <FaShieldAlt className="text-green-400 text-xs" />
              <span className="text-white text-xs font-medium">PCI DSS Secure</span>
            </div>
          </div>

          {/* Accepted cards */}
          <div className="mt-5 flex items-center gap-2">
            <span className="text-blue-200 text-xs mr-1">Accepted:</span>
            <FaCcVisa className="text-white text-2xl" title="Visa" />
            <FaCcMastercard className="text-white text-2xl" title="Mastercard" />
            <FaCcAmex className="text-white text-2xl" title="American Express" />
            <span className="rounded bg-white/15 px-2 py-0.5 text-white text-[10px] font-bold tracking-wider">ZIMSWITCH</span>
          </div>
        </div>

        {/* Body */}
        <div className="px-8 py-7">
          {merchantReference && (
            <div className="mb-5 flex items-center justify-between rounded-xl bg-gray-50 border border-gray-100 px-4 py-3">
              <span className="text-xs text-gray-500">Reference</span>
              <span className="font-mono text-xs font-semibold text-gray-700 tracking-wider">{merchantReference}</span>
            </div>
          )}

          {/* Loading shimmer */}
          {!scriptLoaded && !scriptError && (
            <div className="mb-5 space-y-3 animate-pulse" aria-label="Loading payment form">
              <div className="h-12 rounded-lg bg-gray-100" />
              <div className="flex gap-3">
                <div className="h-12 flex-1 rounded-lg bg-gray-100" />
                <div className="h-12 flex-1 rounded-lg bg-gray-100" />
              </div>
              <div className="h-12 rounded-lg bg-gray-100" />
              <p className="pt-1 text-center text-xs text-gray-400">Loading secure payment widget…</p>
            </div>
          )}

          {/* Error */}
          {scriptError && (
            <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 px-4 py-4">
              <span className="mt-0.5 flex-shrink-0 text-red-500">⚠</span>
              <div>
                <p className="text-sm font-semibold text-red-700">Payment widget failed to load</p>
                <p className="mt-0.5 text-xs text-red-600">{scriptError}</p>
              </div>
            </div>
          )}

          {/* OPPWA widget — styled by their hosted script; we cannot touch internals */}
          <form action={returnUrl} className="paymentWidgets" data-brands={brands} />

          <div className="mt-6 flex flex-col items-center gap-4">
            <Link
              href="/booking"
              className="inline-flex items-center gap-2 text-sm text-gray-400 transition hover:text-gray-700"
            >
              <FaArrowLeft className="text-xs" /> Cancel and return to booking
            </Link>
            <p className="text-center text-[11px] text-gray-300 leading-relaxed">
              Your card details are handled directly by the bank&apos;s secure gateway.<br />
              Kali Safaris never sees or stores your card number.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function CardCheckoutPage() {
  return (
    <Suspense fallback={null}>
      <CardCheckoutContent />
    </Suspense>
  );
}
