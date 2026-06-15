'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';

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
    if (widgetScriptUrl) {
      return widgetScriptUrl;
    }
    if (!checkoutId) {
      return '';
    }
    return `https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId=${encodeURIComponent(checkoutId)}`;
  }, [checkoutId, widgetScriptUrl]);

  useEffect(() => {
    if (!resolvedScriptUrl || !checkoutId) {
      return;
    }

    setScriptLoaded(false);
    setScriptError('');

    const existing = document.querySelector('script[data-copyandpay-widget="1"]');
    if (existing) {
      existing.remove();
    }

    const script = document.createElement('script');
    script.src = resolvedScriptUrl;
    script.async = true;
    script.setAttribute('data-copyandpay-widget', '1');
    script.crossOrigin = 'anonymous';
    if (integrity) {
      script.integrity = integrity;
    }

    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setScriptError('Unable to load secure card widget. Please try again.');

    document.body.appendChild(script);

    return () => {
      script.remove();
    };
  }, [checkoutId, integrity, resolvedScriptUrl]);

  if (!checkoutId || !resolvedScriptUrl) {
    return (
      <main className="min-h-screen bg-linear-to-b from-[#001a33] via-[#002b4d] to-[#001a33] py-16 px-6">
        <div className="mx-auto max-w-2xl rounded-2xl bg-white p-8 shadow-2xl">
          <h1 className="mb-3 text-2xl font-black text-gray-900">Secure Card Checkout</h1>
          <p className="mb-6 text-gray-700">Missing checkout session. Please restart card payment from booking.</p>
          <Link href="/booking" className="inline-block rounded-full border border-gray-300 px-5 py-3 font-semibold text-gray-700 transition hover:bg-gray-50">
            Back to Booking
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-linear-to-b from-[#001a33] via-[#002b4d] to-[#001a33] py-16 px-6">
      <div className="mx-auto max-w-2xl rounded-2xl bg-white p-8 shadow-2xl">
        <h1 className="mb-2 text-2xl font-black text-gray-900">Secure Card Checkout</h1>
        <p className="mb-1 text-gray-700">Complete your card payment on the hosted secure form.</p>
        {merchantReference && (
          <p className="mb-6 text-sm text-gray-500">Merchant reference: <span className="font-semibold text-gray-700">{merchantReference}</span></p>
        )}

        {!scriptLoaded && !scriptError && (
          <p className="mb-4 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
            Loading secure payment widget...
          </p>
        )}

        {scriptError && (
          <p className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {scriptError}
          </p>
        )}

        <form action={returnUrl} className="paymentWidgets" data-brands={brands} />

        <div className="mt-6">
          <Link href="/booking" className="inline-block rounded-full border border-gray-300 px-5 py-3 font-semibold text-gray-700 transition hover:bg-gray-50">
            Cancel and Return to Booking
          </Link>
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
