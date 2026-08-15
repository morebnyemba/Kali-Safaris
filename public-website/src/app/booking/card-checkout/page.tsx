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

  .wpwl-group { margin-bottom: 1.25rem; }

  .wpwl-label {
    display: block;
    margin-bottom: 0.45rem;
    font-size: 0.6875rem;
    font-weight: 700;
    color: #6b7280;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .wpwl-control,
  input.wpwl-control {
    display: block;
    width: 100%;
    padding: 0.8rem 1rem;
    font-size: 0.9375rem;
    color: #111827;
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 0.75rem;
    outline: none;
    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.03);
    transition: border-color 0.15s, box-shadow 0.15s, background-color 0.15s;
    box-sizing: border-box;
  }
  .wpwl-control:hover,
  input.wpwl-control:hover {
    border-color: #cbd5e1;
  }
  .wpwl-control:focus,
  input.wpwl-control:focus,
  .wpwl-control:focus-within {
    border-color: #002b4d;
    box-shadow: 0 0 0 4px rgba(0, 43, 77, 0.1);
    background: #fff;
  }

  /* Cardholder name is a real DOM input (not an iframe) — safe to add an
     icon affordance, matching the icon-in-input pattern used across the
     rest of the booking flow. */
  .wpwl-control.wpwl-control-cardHolder,
  input.wpwl-control-cardHolder {
    padding-left: 2.75rem;
    background-repeat: no-repeat;
    background-position: 0.95rem center;
    background-size: 1rem 1rem;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%239ca3af'%3E%3Cpath d='M12 12a5 5 0 100-10 5 5 0 000 10zm0 2c-4.42 0-8 2.24-8 5v1a1 1 0 001 1h14a1 1 0 001-1v-1c0-2.76-3.58-5-8-5z'/%3E%3C/svg%3E");
  }

  /* The card-number and CVV controls are iframes — style the wrapper div */
  .wpwl-control-cardNumber,
  .wpwl-control-cvv {
    padding: 0 0.35rem;
    overflow: hidden;
    height: 3rem;
    display: flex;
    align-items: center;
  }
  .wpwl-control-cardNumber iframe,
  .wpwl-control-cvv iframe {
    width: 100% !important;
    height: 100% !important;
    border: none;
  }

  /* Expiry + CVV side by side, stacked on very narrow viewports */
  .wpwl-group-expiry,
  .wpwl-group-cvv {
    width: calc(50% - 0.5rem);
    display: inline-block;
    vertical-align: top;
  }
  .wpwl-group-expiry { margin-right: 1rem; }
  @media (max-width: 380px) {
    .wpwl-group-expiry,
    .wpwl-group-cvv {
      width: 100%;
      display: block;
    }
    .wpwl-group-expiry { margin-right: 0; }
  }

  /* Submit button */
  .wpwl-button-pay {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    width: 100%;
    margin-top: 1.5rem;
    padding: 0.95rem 1.5rem;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #001a33 0%, #003366 100%);
    border: none;
    border-radius: 9999px;
    cursor: pointer;
    letter-spacing: 0.02em;
    box-shadow: 0 10px 24px -8px rgba(0, 26, 51, 0.55);
    transition: opacity 0.15s, transform 0.1s, box-shadow 0.15s;
  }
  .wpwl-button-pay::before {
    content: '';
    width: 0.9rem;
    height: 0.9rem;
    flex-shrink: 0;
    background-repeat: no-repeat;
    background-size: contain;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 1a5 5 0 00-5 5v3H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2v-9a2 2 0 00-2-2h-2V6a5 5 0 00-5-5zm-3 8V6a3 3 0 116 0v3H9zm3 3a2 2 0 012 2c0 .74-.4 1.39-1 1.73V17a1 1 0 11-2 0v-1.27c-.6-.34-1-.99-1-1.73a2 2 0 012-2z'/%3E%3C/svg%3E");
  }
  .wpwl-button-pay:hover { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 12px 28px -8px rgba(0, 26, 51, 0.6); }
  .wpwl-button-pay:active { transform: translateY(0); }
  .wpwl-button-pay:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px rgba(232, 96, 10, 0.45), 0 10px 24px -8px rgba(0, 26, 51, 0.55);
  }
  .wpwl-button-pay:disabled,
  .wpwl-button-pay.wpwl-disabled {
    opacity: 0.65;
    cursor: progress;
    transform: none;
  }

  /* Brand selector row — lets the cardholder explicitly pick their card type
     (e.g. Private Label) when it can't be auto-detected from the PAN alone. */
  .wpwl-wrapper-brand {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
  }
  .wpwl-wrapper-brand .wpwl-brand-card {
    width: 3rem;
    height: 1.95rem;
    background: #fff;
    border: 1.5px solid #e5e7eb;
    border-radius: 0.5rem;
    cursor: pointer;
    opacity: 0.55;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    transition: opacity 0.15s, border-color 0.15s, box-shadow 0.15s, transform 0.1s;
  }
  .wpwl-wrapper-brand .wpwl-brand-card:hover {
    opacity: 0.85;
    transform: translateY(-1px);
  }
  .wpwl-wrapper-brand .wpwl-brand-card.wpwl-selected-brand {
    opacity: 1;
    border-color: #E8600A;
    box-shadow: 0 0 0 3px rgba(232, 96, 10, 0.15);
  }

  /* Validation error messages from widget */
  .wpwl-hint {
    display: block;
    margin-top: 0.45rem;
    padding: 0.4rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: #b91c1c;
    background: #fef2f2;
    border-left: 3px solid #ef4444;
    border-radius: 0 0.5rem 0.5rem 0;
  }

  /* Highlight field with error */
  .wpwl-has-error .wpwl-control,
  .wpwl-has-error input.wpwl-control {
    border-color: #ef4444;
    background: #fff5f5;
    box-shadow: none;
  }

  /* Loading spinner OPPWA injects while the widget boots / submits */
  .wpwl-spinner {
    border-top-color: #E8600A !important;
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
      // eslint-disable-next-line no-console
      console.error('[COPYandPAY widget error]', error);
      const name = error?.name || '';
      const code = error?.code || '';
      const msg  = error?.message || '';
      const isExpired =
        name === 'InvalidCheckoutIdError' ||
        msg.includes('No payment session found');
      const isInvalidParam = code === '200.300.404';
      onWidgetError(
        isExpired
          ? 'Your payment session has expired. Sessions last 30 minutes — please go back and start a new payment.'
          : isInvalidParam
            ? 'This card type or payment detail is not supported for this merchant account. Please try a different card.'
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
  const brands = (searchParams.get('brands') || 'PRIVATE_LABEL').trim();
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
    <main className="min-h-screen bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] flex items-center justify-center px-3 py-10 sm:px-4 sm:py-16">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="bg-gradient-to-r from-[#001a33] to-[#003366] px-5 py-6 sm:px-8">
          <div className="flex flex-wrap items-center justify-between gap-y-2 gap-x-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-amber-400/20">
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
          <div className="mt-5 flex flex-wrap items-center gap-x-2 gap-y-1.5">
            <span className="text-blue-200 text-xs mr-1">Accepted:</span>
            <FaCcVisa className="text-white text-2xl" title="Visa" />
            <FaCcMastercard className="text-white text-2xl" title="Mastercard" />
            <FaCcAmex className="text-white text-2xl" title="American Express" />
            {brands.includes('ZIMSWITCH') && (
              <span className="rounded-full bg-white/15 px-2.5 py-1 text-white text-[10px] font-bold tracking-wider ring-1 ring-white/20">ZIMSWITCH</span>
            )}
            {brands.includes('PRIVATE_LABEL') && (
              <span className="rounded-full bg-white/15 px-2.5 py-1 text-white text-[10px] font-bold tracking-wider ring-1 ring-white/20">PRIVATE LABEL</span>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="px-5 py-6 sm:px-8 sm:py-7">
          {merchantReference && (
            <div className="mb-5 flex items-center justify-between gap-2 rounded-xl bg-gray-50 border border-gray-100 px-4 py-3">
              <span className="text-xs text-gray-500 flex-shrink-0">Reference</span>
              <span className="font-mono text-xs font-semibold text-gray-700 tracking-wider truncate">{merchantReference}</span>
            </div>
          )}

          {/* Test mode hint */}
          {resolvedScriptUrl.includes('eu-test.oppwa.com') && (
            <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-2">Test Mode — Use these cards</p>
              {(() => {
                const testCards = [
                  { brand: 'Visa', pan: '4200000000000000', expiry: '05/30', cvv: '123' },
                  { brand: 'Mastercard', pan: '5454545454545454', expiry: '05/30', cvv: '123' },
                  { brand: 'Amex', pan: '375987000000005', expiry: '05/30', cvv: '1234' },
                ].filter(({ brand }) => brands.toUpperCase().includes(brand.toUpperCase()));
                if (testCards.length === 0) {
                  return (
                    <p className="text-xs text-amber-800">
                      This merchant account only accepts {brands} test cards. Contact CBZ/ZimSwitch
                      for a valid test PAN for this brand — the standard VISA/Mastercard/Amex test
                      cards will not work here.
                    </p>
                  );
                }
                return (
                  <div className="space-y-1.5">
                    {testCards.map(({ brand, pan, expiry, cvv }) => (
                      <div key={brand} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-0.5 rounded-lg bg-white/60 px-2.5 py-1.5">
                        <span className="text-xs font-semibold text-amber-800 w-20 flex-shrink-0">{brand}</span>
                        <span className="font-mono text-xs text-amber-900">{pan}</span>
                        <span className="font-mono text-xs text-amber-700">{expiry} / {cvv}</span>
                      </div>
                    ))}
                  </div>
                );
              })()}
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

          <div className="mt-7 border-t border-gray-100 pt-5 flex flex-col items-center gap-4">
            <Link
              href="/booking"
              className="inline-flex items-center gap-2 text-sm text-gray-400 transition hover:text-gray-700"
            >
              <FaArrowLeft className="text-xs" /> Cancel and return to booking
            </Link>
            <div className="flex items-center gap-1.5 text-gray-300">
              <FaShieldAlt className="text-[11px]" />
              <span className="text-[11px] font-semibold tracking-wide uppercase">Secured by ZimSwitch &amp; OPPWA</span>
            </div>
            <p className="text-center text-[11px] text-gray-300 leading-relaxed max-w-xs">
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
