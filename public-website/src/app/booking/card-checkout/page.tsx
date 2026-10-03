'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { FaArrowLeft, FaCcAmex, FaCcMastercard, FaCcVisa, FaExclamationTriangle, FaLock, FaShieldAlt } from 'react-icons/fa';
import type { IconType } from 'react-icons';

/* ── ZimSwitch / OPPWA COPYandPAY hosted card form ─────────────────────────
   The widget script renders the card form; card number and CVV live in
   OPPWA iframes, so only their wrappers and placeholders can be styled.
   wpwlOptions.style = "plain" makes OPPWA ship unstyled markup for us to theme.
──────────────────────────────────────────────────────────────────────────── */
const WIDGET_CSS = `
  .wpwl-form-card { font-family: inherit; margin: 0; padding: 0; background: none; border: 0; box-shadow: none; }
  .wpwl-group { margin-bottom: 1.1rem; }
  .wpwl-label {
    display: block; margin-bottom: 0.4rem;
    font-size: 0.75rem; font-weight: 600; color: #4b5563; letter-spacing: 0.02em;
  }
  .wpwl-control, input.wpwl-control {
    display: block; width: 100%; height: 3rem; padding: 0 1rem;
    font-size: 1rem; color: #111827; background: #fff;
    border: 1.5px solid #e5e7eb; border-radius: 0.75rem; outline: none;
    transition: border-color .15s, box-shadow .15s; box-sizing: border-box;
  }
  .wpwl-control:hover, input.wpwl-control:hover { border-color: #d1d5db; }
  .wpwl-control:focus, input.wpwl-control:focus, .wpwl-control:focus-within {
    border-color: #E8600A; box-shadow: 0 0 0 4px rgba(232, 96, 10, 0.12);
  }
  .wpwl-control-cardNumber, .wpwl-control-cvv { padding: 0 0.35rem; overflow: hidden; display: flex; align-items: center; }
  .wpwl-control-cardNumber iframe, .wpwl-control-cvv iframe { width: 100% !important; height: 100% !important; border: none; }

  .wpwl-group-expiry, .wpwl-group-cvv { width: calc(50% - 0.5rem); display: inline-block; vertical-align: top; }
  .wpwl-group-expiry { margin-right: 1rem; }
  @media (max-width: 360px) {
    .wpwl-group-expiry, .wpwl-group-cvv { width: 100%; display: block; }
    .wpwl-group-expiry { margin-right: 0; }
  }

  .wpwl-button-pay {
    display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    width: 100%; margin-top: 0.5rem; padding: 0.95rem 1.5rem;
    font-size: 1rem; font-weight: 700; color: #fff;
    background: #C8102E; border: none; border-radius: 9999px; cursor: pointer;
    box-shadow: 0 10px 24px -10px rgba(200, 16, 46, 0.6);
    transition: background-color .15s, transform .1s;
  }
  .wpwl-button-pay::before {
    content: ''; width: 0.9rem; height: 0.9rem; flex-shrink: 0;
    background: no-repeat center / contain url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 1a5 5 0 00-5 5v3H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2v-9a2 2 0 00-2-2h-2V6a5 5 0 00-5-5zm-3 8V6a3 3 0 116 0v3H9z'/%3E%3C/svg%3E");
  }
  .wpwl-button-pay:hover { background: #A00D24; }
  .wpwl-button-pay:active { transform: translateY(1px); }
  .wpwl-button-pay:focus-visible { outline: 3px solid rgba(232, 96, 10, 0.5); outline-offset: 2px; }
  .wpwl-button-pay:disabled, .wpwl-button-pay.wpwl-disabled { opacity: .6; cursor: progress; }

  /* The merchant entity is provisioned per brand; there is nothing to choose between. */
  .wpwl-group-brand, .wpwl-label-brand, .wpwl-wrapper-brand { display: none !important; }

  .wpwl-hint { display: block; margin-top: 0.4rem; font-size: 0.75rem; font-weight: 500; color: #b91c1c; }
  .wpwl-has-error .wpwl-control, .wpwl-has-error input.wpwl-control { border-color: #ef4444; background: #fff7f7; }
  .wpwl-spinner { border-top-color: #E8600A !important; }
`;

const DEFAULT_WIDGET_HOST = /(^|\.)oppwa\.com$/i;
const EXTRA_WIDGET_HOSTS = (process.env.NEXT_PUBLIC_PAYMENT_WIDGET_HOSTS || '')
  .split(',').map((h) => h.trim().toLowerCase()).filter(Boolean);

/** Only load the payment script from the gateway — never from a URL someone put in a link. */
function trustedWidgetUrl(raw: string, checkoutId: string): string {
  try {
    const url = new URL(raw);
    const hostOk = DEFAULT_WIDGET_HOST.test(url.hostname) || EXTRA_WIDGET_HOSTS.includes(url.hostname.toLowerCase());
    if (url.protocol !== 'https:' || !hostOk || url.pathname !== '/v1/paymentWidgets.js') return '';
    if (url.searchParams.get('checkoutId') !== checkoutId) return '';
    return url.toString();
  } catch {
    return '';
  }
}

/** The widget redirects to this URL after payment, so keep it on our own site. */
function sameOriginUrl(raw: string, fallback: string): string {
  try {
    const url = new URL(raw, window.location.origin);
    return url.origin === window.location.origin ? url.toString() : fallback;
  } catch {
    return fallback;
  }
}

// OPPWA's published sandbox cards; only shown on the test gateway, for brands this merchant accepts.
const TEST_CARDS: Record<string, { pan: string; cvv: string }> = {
  VISA: { pan: '4200 0000 0000 0000', cvv: '123' },
  MASTER: { pan: '5454 5454 5454 5454', cvv: '123' },
  AMEX: { pan: '3759 870000 00005', cvv: '1234' },
};

const BRAND_DISPLAY: Record<string, { label: string; icon?: IconType }> = {
  VISA: { label: 'Visa', icon: FaCcVisa },
  MASTER: { label: 'Mastercard', icon: FaCcMastercard },
  AMEX: { label: 'American Express', icon: FaCcAmex },
  PRIVATE_LABEL: { label: 'ZimSwitch' },
  ZIMSWITCH: { label: 'ZimSwitch' },
};

function setWpwlOptions(onWidgetError: (msg: string, expired: boolean) => void) {
  // Must be on window before paymentWidgets.js loads.
  (window as Window & { wpwlOptions?: object }).wpwlOptions = {
    style: 'plain',
    iframeStyles: {
      'card-number-placeholder': { color: '#9ca3af', fontSize: '16px', fontFamily: 'inherit' },
      'cvv-placeholder': { color: '#9ca3af', fontSize: '16px', fontFamily: 'inherit' },
    },
    labels: {
      cardHolder: 'Name on card',
      cardNumber: 'Card number',
      cvv: 'Security code (CVV)',
      expiryDate: 'Expiry (MM/YY)',
      submit: 'Pay securely',
    },
    onError(error: { name?: string; code?: string; message?: string }) {
      console.error('[COPYandPAY widget error]', error);
      const msg = error?.message || '';
      const expired = error?.name === 'InvalidCheckoutIdError' || msg.includes('No payment session found');
      onWidgetError(
        expired
          ? 'This payment session has expired (sessions last 30 minutes). Please start the payment again.'
          : error?.code === '200.300.404'
            ? 'This card type isn’t accepted here. Please try another card or payment method.'
            : `The payment form reported an error${msg ? `: ${msg}` : ''}. Please try again.`,
        expired,
      );
    },
  };
}

function Shell({ children, summary }: { children: React.ReactNode; summary?: React.ReactNode }) {
  return (
    <main className="min-h-[calc(100vh-3.5rem)] bg-[#FFF9F5] px-4 py-8 sm:py-12">
      <div className={`mx-auto grid w-full gap-6 ${summary ? 'max-w-4xl lg:grid-cols-[1fr_300px]' : 'max-w-md'}`}>
        <div className="order-2 lg:order-1">{children}</div>
        {summary && <aside className="order-1 lg:order-2">{summary}</aside>}
      </div>
    </main>
  );
}

function ErrorCard({ title, message }: { title: string; message: string }) {
  return (
    <Shell>
      <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <span className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-red-50 text-red-600"><FaExclamationTriangle aria-hidden /></span>
        <h1 className="text-lg font-bold text-gray-900">{title}</h1>
        <p className="mt-2 text-sm text-gray-600">{message}</p>
        <Link href="/booking" className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#C8102E] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#A00D24]">
          <FaArrowLeft className="text-xs" aria-hidden /> Back to booking
        </Link>
      </div>
    </Shell>
  );
}

function CardCheckoutContent() {
  const searchParams = useSearchParams();
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState('');
  const [widgetError, setWidgetError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [returnUrl, setReturnUrl] = useState('');

  const checkoutId = (searchParams.get('checkoutId') || '').trim();
  const merchantReference = (searchParams.get('merchantRef') || '').trim();
  const brands = (searchParams.get('brands') || 'PRIVATE_LABEL').trim().toUpperCase();
  const integrity = (searchParams.get('integrity') || '').trim();
  const amount = Number(searchParams.get('amount') || '');
  const item = (searchParams.get('item') || '').trim();
  const rawReturnUrl = (searchParams.get('returnUrl') || '').trim();

  const widgetUrl = useMemo(() => {
    if (!checkoutId) return '';
    const raw = (searchParams.get('widget') || '').trim()
      || `https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId=${encodeURIComponent(checkoutId)}`;
    return trustedWidgetUrl(raw, checkoutId);
  }, [checkoutId, searchParams]);
  const isTestGateway = widgetUrl.includes('test.oppwa.com');
  const brandList = brands.split(/[\s,]+/).filter(Boolean);

  // window is only available after mount.
  useEffect(() => {
    const fallback = `${window.location.origin}/booking/payment-status?channel=card`;
    setReturnUrl(rawReturnUrl ? sameOriginUrl(rawReturnUrl, fallback) : fallback); // eslint-disable-line react-hooks/set-state-in-effect
  }, [rawReturnUrl]);

  useEffect(() => {
    if (!widgetUrl) return;
    if (!document.getElementById('wpwl-custom-styles')) {
      const style = document.createElement('style');
      style.id = 'wpwl-custom-styles';
      style.textContent = WIDGET_CSS;
      document.head.appendChild(style);
    }
    setWpwlOptions((msg, expired) => {
      setWidgetError(msg);
      setSessionExpired(expired);
    });

    document.querySelector('script[data-copyandpay-widget="1"]')?.remove();
    const script = document.createElement('script');
    script.src = widgetUrl;
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.setAttribute('data-copyandpay-widget', '1');
    if (integrity) script.integrity = integrity;
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setScriptError('The secure card form could not load. Check your connection and refresh the page.');
    document.body.appendChild(script);
    return () => { script.remove(); };
  }, [widgetUrl, integrity]);

  if (!checkoutId) {
    return <ErrorCard title="No payment in progress" message="We couldn't find a card payment session. Please start the payment again from your booking." />;
  }
  if (!widgetUrl) {
    return <ErrorCard title="We couldn't verify this payment page" message="This link doesn't point to our payment provider, so we haven't loaded a card form. Please start the payment again from your booking." />;
  }

  const summary = (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm lg:sticky lg:top-20">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gray-400">Your booking</p>
      {item && <p className="mt-1 text-base font-bold text-gray-900">{item}</p>}
      {merchantReference && (
        <p className="mt-2 flex items-center justify-between gap-3 text-xs text-gray-500">
          Reference <span className="truncate font-mono font-semibold text-gray-700">{merchantReference}</span>
        </p>
      )}
      {Number.isFinite(amount) && amount > 0 && (
        <div className="mt-4 flex items-baseline justify-between border-t border-gray-100 pt-4">
          <span className="text-sm font-medium text-gray-600">Amount</span>
          <span className="text-2xl font-black tabular-nums text-gray-900">USD {amount.toFixed(2)}</span>
        </div>
      )}
      <ul className="mt-4 space-y-2 border-t border-gray-100 pt-4 text-xs text-gray-500">
        <li className="flex items-center gap-2"><FaLock className="text-emerald-600" aria-hidden /> Encrypted connection</li>
        <li className="flex items-center gap-2"><FaShieldAlt className="text-emerald-600" aria-hidden /> Card handled by ZimSwitch — never by Kalai Safaris</li>
      </ul>
    </div>
  );

  return (
    <Shell summary={summary}>
      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-5 py-4 sm:px-6">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Pay by card</h1>
            <p className="text-xs text-gray-500">Secure payment page provided by ZimSwitch</p>
          </div>
          <ul className="flex items-center gap-1.5" aria-label="Accepted cards">
            {brandList.map((code) => {
              const brand = BRAND_DISPLAY[code] || { label: code.replace(/_/g, ' ') };
              return brand.icon ? (
                <li key={code}><brand.icon className="text-3xl text-gray-700" title={brand.label} aria-label={brand.label} /></li>
              ) : (
                <li key={code} className="rounded-md border border-gray-300 px-2 py-1 text-[11px] font-bold tracking-wider text-gray-700">{brand.label.toUpperCase()}</li>
              );
            })}
          </ul>
        </div>

        <div className="px-5 py-6 sm:px-6">
          {isTestGateway && (
            <p className="mb-5 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs text-amber-900">
              <span className="rounded bg-amber-200 px-1.5 text-[10px] font-bold uppercase tracking-wider">Test</span>
              <span>
                Test gateway — no real money is taken.{' '}
                {brandList.some((c) => TEST_CARDS[c])
                  ? brandList.filter((c) => TEST_CARDS[c]).map((c) => `${BRAND_DISPLAY[c].label} ${TEST_CARDS[c].pan}, any future expiry, CVV ${TEST_CARDS[c].cvv}`).join(' · ')
                  : `Use the test card your acquirer issued for ${brandList.map((c) => BRAND_DISPLAY[c]?.label || c).join(', ')}.`}
              </span>
            </p>
          )}

          {!scriptLoaded && !scriptError && !widgetError && (
            <div className="space-y-4 animate-pulse" role="status" aria-label="Loading the secure card form">
              {[0, 1].map((i) => (
                <div key={i}><div className="mb-2 h-3 w-24 rounded bg-gray-200" /><div className="h-12 rounded-xl bg-gray-100" /></div>
              ))}
              <div className="flex gap-4"><div className="h-12 flex-1 rounded-xl bg-gray-100" /><div className="h-12 flex-1 rounded-xl bg-gray-100" /></div>
              <div className="h-12 rounded-full bg-gray-200" />
            </div>
          )}

          {(scriptError || widgetError) && (
            <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <FaExclamationTriangle className="mt-0.5 shrink-0 text-red-500" aria-hidden />
              <div>
                <p className="text-sm font-semibold text-red-800">{sessionExpired ? 'Payment session expired' : 'Something went wrong'}</p>
                <p className="mt-0.5 text-sm text-red-700">{scriptError || widgetError}</p>
                {(sessionExpired || scriptError) && (
                  <Link href="/booking" className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-[#C8102E] px-4 py-2 text-xs font-semibold text-white hover:bg-[#A00D24]">
                    <FaArrowLeft className="text-[10px]" aria-hidden /> Start again
                  </Link>
                )}
              </div>
            </div>
          )}

          {!widgetError && returnUrl && <form action={returnUrl} className="paymentWidgets" data-brands={brands} />}

          <div className="mt-6 border-t border-gray-100 pt-5 text-center">
            <Link href="/booking" className="inline-flex items-center gap-2 text-sm text-gray-500 transition hover:text-gray-900">
              <FaArrowLeft className="text-xs" aria-hidden /> Cancel and choose another payment method
            </Link>
          </div>
        </div>
      </div>
    </Shell>
  );
}

export default function CardCheckoutPage() {
  return (
    <Suspense fallback={null}>
      <CardCheckoutContent />
    </Suspense>
  );
}
