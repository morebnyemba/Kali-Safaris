'use client';

/**
 * 3DS v1 ACS redirect page for CBZ/iVeri direct card payments.
 *
 * Flow:
 *   1. cbz_card_debit_view returns { requires_3ds: true, challenge: { ACSURL, PaReq, MD, TermUrl } }
 *   2. Frontend stores challenge data in sessionStorage and navigates here.
 *   3. This page auto-submits a hidden form to the ACS URL (bank authentication page).
 *   4. ACS authenticates the cardholder then POSTs back to TermUrl (/api/3ds/callback).
 *   5. /api/3ds/callback redirects to /booking/payment-status which calls
 *      /crm-api/payments/cbz/card/3ds/complete/ with the PaRes.
 *
 * Challenge data is read from sessionStorage key "kali_3ds_challenge" (JSON).
 * Expected shape:
 *   { ACSURL: string, PaReq: string, MD: string, TermUrl: string }
 */

import { Suspense, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { FaArrowLeft, FaExclamationTriangle, FaLock, FaShieldAlt } from 'react-icons/fa';

const CHALLENGE_KEY = 'kali_3ds_challenge';

interface ChallengeData {
  ACSURL?: string;
  ACSUrl?: string;
  AcsUrl?: string;
  PaReq?: string;
  PAREQ?: string;
  MD?: string;
  TermUrl?: string;
  TermURL?: string;
}

function ThreeDSChallengeContent() {
  const formRef = useRef<HTMLFormElement>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Run after mount so state updates aren't synchronous in the effect body.
    let submitTimer = 0;
    const startTimer = window.setTimeout(() => {
    let raw = '';
    try {
      raw = window.sessionStorage.getItem(CHALLENGE_KEY) ?? '';
    } catch {
      setError('Unable to read 3DS challenge data. Please go back and try again.');
      return;
    }

    if (!raw) {
      setError('No 3DS challenge data found. Please return to checkout.');
      return;
    }

    let challenge: ChallengeData;
    try {
      challenge = JSON.parse(raw) as ChallengeData;
    } catch {
      setError('Invalid 3DS challenge data. Please return to checkout.');
      return;
    }

    const acsUrl = challenge.ACSURL || challenge.ACSUrl || challenge.AcsUrl || '';
    const paReq = challenge.PaReq || challenge.PAREQ || '';
    const md = challenge.MD || '';
    const termUrl = challenge.TermUrl || challenge.TermURL || '';

    if (!acsUrl || !paReq) {
      setError('Incomplete 3DS challenge data (missing ACSURL or PaReq). Please return to checkout.');
      return;
    }

    const form = formRef.current;
    if (!form) return;

    // Populate the hidden form fields
    (form.querySelector('[name="PaReq"]') as HTMLInputElement).value = paReq;
    (form.querySelector('[name="MD"]') as HTMLInputElement).value = md;
    (form.querySelector('[name="TermUrl"]') as HTMLInputElement).value = termUrl;
    form.action = acsUrl;

    // Remove challenge from storage before redirect so it isn't replayed
    try {
      window.sessionStorage.removeItem(CHALLENGE_KEY);
    } catch {
      // Non-critical
    }

    setSubmitting(true);
    // Small delay so the "Redirecting…" message renders before the browser navigates
    submitTimer = window.setTimeout(() => form.submit(), 150);
    }, 0);
    return () => {
      window.clearTimeout(startTimer);
      window.clearTimeout(submitTimer);
    };
  }, []);

  return (
    <main className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center bg-[#FFF9F5] px-4 py-12">
      <section className="w-full max-w-md overflow-hidden rounded-3xl border border-gray-200 bg-white text-center shadow-[0_20px_50px_-30px_rgba(0,0,0,0.35)]" aria-live="polite">
        {error ? (
          <div className="px-8 py-10">
            <span className="mx-auto mb-5 flex size-16 items-center justify-center rounded-full bg-red-50 text-[#C8102E] ring-8 ring-red-50/60">
              <FaExclamationTriangle size={26} aria-hidden />
            </span>
            <h1 className="text-xl font-black text-gray-900">We couldn’t start card verification</h1>
            <p className="mt-2 text-sm text-gray-600">{error}</p>
            <Link href="/booking" className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#C8102E] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#A00D24]">
              <FaArrowLeft className="text-xs" aria-hidden /> Back to checkout
            </Link>
          </div>
        ) : (
          <div className="px-8 py-10">
            <span className="relative mx-auto mb-6 flex size-20 items-center justify-center">
              <span className="absolute inset-0 animate-spin rounded-full border-4 border-orange-100 border-t-[#E8600A]" aria-hidden />
              <FaShieldAlt className="text-[#E8600A]" size={28} aria-hidden />
            </span>
            <h1 className="text-xl font-black text-gray-900">Verifying your card</h1>
            <p className="mt-2 text-sm text-gray-600">
              {submitting ? 'Taking you to your bank’s secure page…' : 'Preparing secure verification…'}
            </p>
            <ol className="mx-auto mt-6 max-w-xs space-y-2 text-left text-sm text-gray-600">
              <li className="flex gap-3"><span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-gray-900 text-[11px] font-bold text-white">1</span>Your bank may ask for a code or app approval.</li>
              <li className="flex gap-3"><span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-gray-900 text-[11px] font-bold text-white">2</span>You’ll come back here automatically.</li>
            </ol>
            <p className="mt-6 flex items-center justify-center gap-1.5 text-xs text-gray-400"><FaLock aria-hidden /> Don’t close or refresh this page</p>
          </div>
        )}
        {/* Hidden ACS redirect form — populated and submitted by useEffect */}
        <form ref={formRef} method="POST" style={{ display: 'none' }}>
          <input type="hidden" name="PaReq" defaultValue="" />
          <input type="hidden" name="MD" defaultValue="" />
          <input type="hidden" name="TermUrl" defaultValue="" />
        </form>
      </section>
    </main>
  );
}

export default function ThreeDSChallengePage() {
  return (
    <Suspense fallback={null}>
      <ThreeDSChallengeContent />
    </Suspense>
  );
}
