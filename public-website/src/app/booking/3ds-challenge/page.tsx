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
import { FaLock } from 'react-icons/fa';

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
    const id = window.setTimeout(() => form.submit(), 150);
    return () => window.clearTimeout(id);
  }, []);

  if (error) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl p-8">
          <div className="flex items-center gap-3 mb-4">
            <FaLock className="text-red-500 text-xl" />
            <h1 className="text-lg font-bold text-gray-900">3D Secure Error</h1>
          </div>
          <p className="text-red-600 text-sm mb-6">{error}</p>
          <a
            href="/booking"
            className="inline-flex items-center gap-2 rounded-full bg-[#001a33] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#003366]"
          >
            ← Back to Checkout
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl p-8 text-center">
        <div className="flex justify-center mb-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#001a33]">
            <FaLock className="text-amber-400 text-2xl" />
          </div>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">3D Secure Authentication</h1>
        <p className="text-gray-500 text-sm mb-6">
          {submitting
            ? 'Redirecting you to your bank to verify your card…'
            : 'Preparing secure authentication…'}
        </p>
        {submitting && (
          <div className="flex justify-center">
            <span className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#001a33] border-t-transparent" />
          </div>
        )}
        {/* Hidden ACS redirect form — populated and submitted by useEffect */}
        <form ref={formRef} method="POST" style={{ display: 'none' }}>
          <input type="hidden" name="PaReq" defaultValue="" />
          <input type="hidden" name="MD" defaultValue="" />
          <input type="hidden" name="TermUrl" defaultValue="" />
        </form>
      </div>
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
