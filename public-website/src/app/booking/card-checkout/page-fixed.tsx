'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FaCcVisa, FaCcMastercard, FaCcAmex,
  FaLock, FaShieldAlt, FaArrowLeft,
} from 'react-icons/fa';

/* ── Widget CSS overrides injected once into <head> ───────────────────────
   Requires wpwlOptions.style = "plain" so OPPWA ships unstyled markup.
   We cannot touch inside card-number/CVV iframes — only iframeStyles
   (placeholder colour/font) works there.
──────────────────────────────────────────────────────────────────────────── */
const WIDGET_CSS = `
  .wpwl-form-card { font-family: inherit; }

  .wpwl-group { margin-bottom: 1rem; }

  .wpwl-label {
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #374151;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .wpwl-control,
  input.wpwl-control {
    display: block;
    width: 100%;
    padding: 0.65rem 0.85rem;
    font-size: 0.9375rem;
    color: #111827;
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 0.625rem;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    box-sizing: border-box;
  }
  .wpwl-control:focus,
  input.wpwl-control:focus {
    border-color: #002b4d;
    box-shadow: 0 0 0 3px rgba(0,43,77,0.12);
    background: #fff;
  }

  /* The card-number and CVV controls are iframes — style the wrapper div */
  .wpwl-control-cardNumber,
  .wpwl-control-cvv {
    padding: 0;
    overflow: hidden;
    height: 2.75rem;
    display: flex;
    align-items: center;
  }
  .wpwl-control-cardNumber iframe,
  .wpwl-control-cvv iframe {
    width: 100% !important;
    height: 100% !important;
    border: none;
  }

  /* Expiry + CVV side by side */
  .wpwl-group-expiry,
  .wpwl-group-cvv {
    width: 48%;
    display: inline-block;
  }
  .wpwl-group-expiry { margin-right: 4%; }

  /* Submit button */
  .wpwl-button-pay {
    display: block;
    width: 100%;
    margin-top: 1.25rem;
    padding: 0.8rem 1.5rem;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #001a33 0%, #003366 100%);
    border: none;
    border-radius: 9999px;
    cursor: pointer;
    letter-spacing: 0.02em;
    transition: opacity 0.15s, transform 0.1s;
  }
  .wpwl-button-pay:hover { opacity: 0.88; transform: translateY(-1px); }
  .wpwl-button-pay:active { transform: translateY(0); }

  /* Hide the brand logo row — we show our own icons in the header */
  .wpwl-wrapper-brand { display: none; }

  /* Validation error messages from widget */
  .wpwl-hint {
    display: block;
    margin-top: 0.35rem;
    padding: 0.3rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: #b91c1c;
    background: #fef2f2;
    border-left: 3px solid #ef4444;
    border-radius: 0 0.375rem 0.375rem 0;
  }

  /* Highlight field with error */
  .wpwl-has-error .wpwl-control,
  .wpwl-has-error input.wpwl-control {
    border-color: #ef4444;
    background: #fff5f5;
  }
`;

function injectWidgetStyles() {
  if (document.getElementById('wpwl-custom-styles')) return;
  const style = document.createElement('style');
  style.id = 'wpwl-custom-styles';
  style.textContent = WIDGET_CSS;
  document.head.appendChild(style);
}

function setWpwlOptions(onWidgetError: (msg: string, expired: boolean) => void) {
  // Must be set on window BEFORE the paymentWidgets.js script loads
  (window as Window & { wpwlOptions?: object }).wpwlOptions = {
    style: 'plain',
    iframeStyles: {
      'card-number-placeholder': { color: '#9ca3af', fontSize: '15px', fontFamily: 'inherit' },
      'cvv-placeholder':         { color: '#9ca3af', fontSize: '15px', fontFamily: 'inherit' },
    },
    labels: {
      cardHolder:  'Name on Card',
      cardNumber:  'Card Number',
      cvv:         'CVV / CVC (optional for some cards)',
      expiryDate:  'Expiry Date (MM/YY)',
      submit:      'Pay Securely',
    },
    onError: function(error: { name?: string; code?: string; message?: string }) {
      const name = error?.name || '';
      const code = error?.code || '';
      const msg  = error?.message || '';
      const isExpired =
        name === 'InvalidCheckoutIdError' ||
        code === '200.300.404' ||
        msg.includes('No payment session found');
      onWidgetError(
        isExpired
          ? 'Your payment session has expired. Sessions last 30 minutes — please go back and start a new payment.'
          : `Payment error: ${msg || code || name || 'Unknown error'}. Please try again.`,
        isExpired,
      );
    },
  };
}


function CardCheckoutContent() {
  const searchParams = useSearchParams();
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState('');
  const [widgetError, setWidgetError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);

  const checkoutId = (searchParams.get('checkoutId') || '').trim();
  const merchantReference = (searchParams.get('merchantRef') || '').trim();
  const brands = (searchParams.get('brands') || 'VISA MASTER AMEX').trim();
  const widgetScriptUrl = (searchParams.get('widget') || '').trim();
  const integrity = (searchParams.get('integrity') || '').trim();
  let returnUrl = (searchParams.get('returnUrl') || '/booking/payment-status?channel=card').trim();

  // Store checkoutId in sessionStorage so payment-status can retrieve it for polling
  useEffect(() => {
    if (checkoutId && typeof window !== 'undefined') {
      window.sessionStorage.setItem('kalai_copyandpay_checkout_id', checkoutId);
    }
  }, [checkoutId]);

  // Add checkoutId to returnUrl if it's not already there
  if (checkoutId && !returnUrl.includes('checkoutId=')) {
    const separator = returnUrl.includes('?') ? '&' : '?';
    returnUrl = `${returnUrl}${separator}checkoutId=${encodeURIComponent(checkoutId)}`;
  }

  const resolvedScriptUrl = useMemo(() => {
    if (widgetScriptUrl) return widgetScriptUrl;
    if (!checkoutId) return '';
    return `https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId=${encodeURIComponent(checkoutId)}`;
  }, [checkoutId, widgetScriptUrl]);

  useEffect(() => {
    if (!resolvedScriptUrl || !checkoutId) return;

    setScriptLoaded(false);
    setScriptError('');

    // Inject styles and set options BEFORE the script loads
    injectWidgetStyles();
    setWpwlOptions((msg, expired) => {
      setWidgetError(msg);
      setSessionExpired(expired);
    });

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
            {brands.includes('ZIMSWITCH') && (
              <span className="rounded bg-white/15 px-2 py-0.5 text-white text-[10px] font-bold tracking-wider">ZIMSWITCH</span>
            )}
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

          {/* Test mode hint */}
          {resolvedScriptUrl.includes('eu-test.oppwa.com') && (
            <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-2">Test Mode — Use these cards</p>
              <div className="space-y-1">
                {[
                  { brand: 'Visa', pan: '4200000000000000', expiry: '05/30', cvv: '123' },
                  { brand: 'Mastercard', pan: '5454545454545454', expiry: '05/30', cvv: '123' },
                  { brand: 'Amex', pan: '375987000000005', expiry: '05/30', cvv: '1234' },
                ].map(({ brand, pan, expiry, cvv }) => (
                  <div key={brand} className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-amber-800 w-20">{brand}</span>
                    <span className="font-mono text-xs text-amber-900">{pan}</span>
                    <span className="font-mono text-xs text-amber-700">{expiry} / {cvv}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Loading shimmer */}
          {!scriptLoaded && !scriptError && (
            <div className="mb-5 space-y-3 animate-pulse" aria-label="Loading payment form">
              <div className="h-4 w-24 rounded bg-gray-200" />
              <div className="h-11 rounded-xl bg-gray-100" />
              <div className="h-4 w-20 rounded bg-gray-200" />
              <div className="flex gap-3">
                <div className="h-11 flex-1 rounded-xl bg-gray-100" />
                <div className="h-11 flex-1 rounded-xl bg-gray-100" />
              </div>
              <div className="h-4 w-28 rounded bg-gray-200" />
              <div className="h-11 rounded-xl bg-gray-100" />
              <div className="mt-2 h-12 rounded-full bg-gray-200" />
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

          {/* Widget-level error (e.g. session expired) */}
          {widgetError && (
            <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 px-4 py-4">
              <span className="mt-0.5 flex-shrink-0 text-red-500">⚠</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-700">
                  {sessionExpired ? 'Payment session expired' : 'Payment error'}
                </p>
                <p className="mt-0.5 text-xs text-red-600">{widgetError}</p>
                {sessionExpired && (
                  <Link
                    href="/booking"
                    className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-[#001a33] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#003366]"
                  >
                    <FaArrowLeft className="text-[10px]" /> Start a new payment
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* OPPWA widget — styled via wpwlOptions + injected CSS above */}
          {!widgetError && <form action={returnUrl} className="paymentWidgets" data-brands={brands} />}

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
