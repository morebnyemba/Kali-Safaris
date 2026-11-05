'use client';

import { Suspense, use, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { FaCheckCircle, FaIdCard, FaLock, FaWhatsapp } from 'react-icons/fa';
import BookingModal from '@/components/BookingModal';
import { whatsappLink } from '@/lib/site';

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;

interface Traveler {
  id: string;
  name: string;
  age: number;
  id_required: boolean;
  has_document: boolean;
  has_id_number: boolean;
  needs_id: boolean;
}

interface PaymentRow {
  date: string;
  amount: string;
  currency: string;
  method: string;
  status: string;
  status_display: string;
}

interface Summary {
  booking_reference: string;
  tour_name: string;
  start_date: string;
  departure: string;
  customer_name: string;
  payment_status: string;
  payment_status_display: string;
  total_amount: string;
  amount_paid: string;
  balance_due: string;
  minimum_payment: string;
  balance_due_by: string | null;
  balance_overdue: boolean;
  on_hold: boolean;
  held_from_date: string | null;
  can_reschedule: boolean;
  reschedule_from: string;
  tour_id: number | null;
  can_pay: boolean;
  can_upload: boolean;
  trip_is_over: boolean;
  passengers_booked: number;
  id_required_from_age: number;
  travelers: Traveler[];
  payments: PaymentRow[];
}

const money = (value: string | number, currency = 'USD') =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(Number(value) || 0);

const longDate = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' });

/** Phone photos are often 4–12 MB: shrink to a sharp 2000px JPEG before upload. PDFs pass through. */
async function prepareDocument(file: File): Promise<Blob> {
  if (!file.type.startsWith('image/') || file.size < 1.5 * 1024 * 1024) return file;
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, 2000 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext('2d')?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85));
    return blob ?? file;
  } catch {
    return file;
  }
}

function TravelerIdCard({ traveler, token, canUpload, onUpdated }: {
  traveler: Traveler;
  token: string;
  canUpload: boolean;
  onUpdated: (summary: Summary) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [idNumber, setIdNumber] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const upload = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!file && !idNumber.trim()) {
      setError('Choose a photo or enter the ID number.');
      return;
    }
    setBusy(true);
    try {
      const body = new FormData();
      if (file) {
        const prepared = await prepareDocument(file);
        if (prepared.size > MAX_UPLOAD_BYTES) throw new Error('That file is too large (8 MB max). Please take a smaller photo.');
        body.append('document', prepared, file.type === 'application/pdf' ? 'id.pdf' : 'id.jpg');
      }
      if (idNumber.trim()) body.append('id_number', idNumber.trim());
      const res = await fetch(`${API_BASE}/crm-api/customer-data/manage/${encodeURIComponent(token)}/travelers/${traveler.id}/id/`, {
        method: 'POST',
        body,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Upload failed. Please try again.');
      setFile(null);
      setIdNumber('');
      onUpdated(data as Summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  const done = !traveler.needs_id;
  return (
    <li className="rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-gray-900">{traveler.name}</p>
          <p className="text-sm text-gray-500">Age {traveler.age}{!traveler.id_required && ' · ID optional under 12'}</p>
        </div>
        {done ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
            <FaCheckCircle aria-hidden /> {traveler.id_required ? 'ID received' : 'Not needed'}
          </span>
        ) : (
          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">ID needed</span>
        )}
      </div>

      {!done && canUpload && (
        <form onSubmit={upload} className="mt-4 space-y-3">
          {!traveler.has_document && (
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-gray-700">Photo of ID or passport</span>
              <input
                type="file"
                accept="image/jpeg,image/png,application/pdf"
                aria-label={`ID or passport photo for ${traveler.name}`}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-gray-700 file:mr-3 file:rounded-full file:border-0 file:bg-gray-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              />
              <span className="mt-1 block text-xs text-gray-500">JPG, PNG or PDF. Make sure the name and number are readable.</span>
            </label>
          )}
          {!traveler.has_id_number && (
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-gray-700">ID or passport number</span>
              <input
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                maxLength={50}
                autoComplete="off"
                aria-label={`ID or passport number for ${traveler.name}`}
                className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-[#C8102E] focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20"
              />
            </label>
          )}
          {error && <p role="alert" className="text-sm text-[#C8102E]">{error}</p>}
          <button type="submit" disabled={busy}
            className="w-full rounded-full bg-[#C8102E] px-5 py-2.5 font-bold text-white transition hover:bg-[#A00D24] disabled:opacity-60">
            {busy ? 'Uploading…' : `Save ${traveler.name.split(' ')[0]}'s ID`}
          </button>
        </form>
      )}
    </li>
  );
}

interface SlotAvailability {
  start: string;
  end: string | null;
  display: string;
  departed: boolean;
  seats_left: number | null;
}

/** On-hold bookings: the customer picks a new date (and departure) for the credit they've paid. */
function RescheduleCard({ summary, token, onUpdated }: { summary: Summary; token: string; onUpdated: (s: Summary) => void }) {
  const [date, setDate] = useState('');
  const [slots, setSlots] = useState<SlotAvailability[] | null>(null);
  const [time, setTime] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const party = summary.passengers_booked;

  useEffect(() => {
    if (!date || !summary.tour_id) return;
    let cancelled = false;
    fetch(`${API_BASE}/crm-api/tours/${summary.tour_id}/availability/?date=${encodeURIComponent(date)}`, { cache: 'no-store' })
      .then((res) => res.json())
      .then((data: { success?: boolean; slots?: SlotAvailability[] }) => {
        if (cancelled) return;
        const open = (data.slots ?? []).filter((s) => !s.departed && (s.seats_left === null || s.seats_left >= party));
        setSlots(open);
        setTime(open.length === 1 ? open[0].start : '');
      })
      .catch(() => { if (!cancelled) setSlots([]); });
    return () => { cancelled = true; };
  }, [date, summary.tour_id, party]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/crm-api/customer-data/manage/${encodeURIComponent(token)}/reschedule/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time: time || undefined }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "We couldn't move your booking. Please try another date.");
      onUpdated(data as Summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We couldn't move your booking.");
    } finally {
      setBusy(false);
    }
  };

  const needsTime = slots !== null && slots.length > 0;
  const noRoom = slots !== null && slots.length === 0;

  return (
    <section aria-labelledby="hold-title" className="rounded-2xl border-2 border-[#E8600A]/40 bg-white p-5 shadow-sm">
      <h2 id="hold-title" className="text-lg font-bold text-gray-900">Choose a new date</h2>
      <p className="mt-1 text-sm text-gray-600">
        The balance wasn&apos;t paid in time, so your booking{summary.held_from_date && ` for ${longDate(summary.held_from_date)}`} is on hold
        and those seats were released. <strong>The {money(summary.amount_paid)} you paid is kept as credit.</strong> Pick a new date and pay the
        remaining {money(summary.balance_due)}.
      </p>
      {summary.can_reschedule ? (
        <form onSubmit={submit} className="mt-4 space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-gray-700">New date</span>
            <input type="date" min={summary.reschedule_from} value={date} required
              onChange={(e) => { setDate(e.target.value); setSlots(null); setTime(''); }}
              className="w-full rounded-xl border border-gray-300 px-4 py-2.5 focus:border-[#C8102E] focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20" />
            <span className="mt-1 block text-xs text-gray-500">From {longDate(summary.reschedule_from)} onwards.</span>
          </label>
          {noRoom && date && (
            <p className="text-sm text-[#C8102E]">No departure that day has {party} seat{party === 1 ? '' : 's'} left. Please try another date.</p>
          )}
          {needsTime && slots.length > 1 && (
            <fieldset>
              <legend className="mb-1.5 text-sm font-medium text-gray-700">Departure</legend>
              <div className="grid grid-cols-2 gap-2">
                {slots.map((s) => (
                  <button key={s.start} type="button" onClick={() => setTime(s.start)} aria-pressed={time === s.start}
                    className={`rounded-xl border-2 px-3 py-2 text-left text-sm ${time === s.start ? 'border-[#E8600A] bg-[#FFF9F5]' : 'border-gray-200'}`}>
                    <span className="block font-semibold tabular-nums">{s.display || s.start}</span>
                    {s.seats_left !== null && <span className="text-xs text-gray-500">{s.seats_left} seats left</span>}
                  </button>
                ))}
              </div>
            </fieldset>
          )}
          {error && <p role="alert" className="text-sm text-[#C8102E]">{error}</p>}
          <button type="submit" disabled={busy || !date || noRoom || (needsTime && !time) || slots === null}
            className="w-full rounded-full bg-[#C8102E] px-5 py-3 font-bold text-white transition hover:bg-[#A00D24] disabled:opacity-50">
            {busy ? 'Moving your booking…' : 'Move my booking to this date'}
          </button>
        </form>
      ) : (
        <a href={whatsappLink(`Hi, I'd like to choose a new date for booking ${summary.booking_reference}.`)} target="_blank" rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-[#25D366] px-6 py-3 font-bold text-white hover:bg-[#1EBE5A]">
          <FaWhatsapp aria-hidden /> Choose a date with us on WhatsApp
        </a>
      )}
    </section>
  );
}

function ManageBookingContent({ token }: { token: string }) {
  const searchParams = useSearchParams();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState('');
  const [amount, setAmount] = useState(searchParams.get('amount') ?? '');
  const [payAmount, setPayAmount] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/crm-api/customer-data/manage/${encodeURIComponent(token)}/`, { cache: 'no-store' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "We couldn't load this booking.");
      setSummary(data as Summary);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : "We couldn't load this booking.");
    }
  }, [token]);

  useEffect(() => {
    void load();
    // Coming back from a payment in another tab or app: show the new balance.
    const onFocus = () => { void load(); };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [load]);

  const balance = Number(summary?.balance_due ?? 0);
  const minimum = Number(summary?.minimum_payment ?? 0);
  const amountValue = Number(amount);
  const amountError = useMemo(() => {
    if (!amount) return '';
    if (!Number.isFinite(amountValue) || amountValue <= 0) return 'Enter an amount in US dollars.';
    if (amountValue > balance + 0.001) return `The most you can pay is the balance of ${money(balance)}.`;
    if (amountValue < minimum - 0.001) return `The smallest instalment is ${money(minimum)}.`;
    return '';
  }, [amount, amountValue, balance, minimum]);

  if (error && !summary) {
    return (
      <div className="mx-auto max-w-lg rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <FaLock className="mx-auto mb-3 text-3xl text-gray-400" aria-hidden />
        <h1 className="text-xl font-bold text-gray-900">This link isn&apos;t working</h1>
        <p className="mt-2 text-gray-600">{error}</p>
        <a href={whatsappLink("Hi, my booking link isn't working. Please send me a new one.")} target="_blank" rel="noopener noreferrer"
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#25D366] px-6 py-3 font-bold text-white hover:bg-[#1EBE5A]">
          <FaWhatsapp aria-hidden /> Ask for a new link
        </a>
      </div>
    );
  }

  if (!summary) {
    return <div className="mx-auto h-64 max-w-2xl animate-pulse rounded-2xl bg-gray-100" aria-label="Loading your booking" />;
  }

  if (payAmount !== null) {
    return (
      <div className="mx-auto max-w-3xl">
        <button type="button" onClick={() => { setPayAmount(null); void load(); }} className="mb-4 text-sm font-semibold text-gray-600 hover:text-gray-900">
          ← Back to my booking
        </button>
        <BookingModal
          key={payAmount}
          isOpen
          onClose={() => { setPayAmount(null); void load(); }}
          cruiseType={summary.tour_name}
          amountUsd={payAmount}
          initialBookingReference={summary.booking_reference}
          manageToken={token}
          fixedAmountUsd={payAmount}
          presentation="page"
        />
      </div>
    );
  }

  const missing = summary.travelers.filter((t) => t.needs_id);
  const unlisted = summary.passengers_booked - summary.travelers.length;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-[#E8600A]">Your booking</p>
        <h1 className="mt-1 text-3xl font-bold text-gray-900">{summary.tour_name}</h1>
        <p className="mt-1 text-gray-600">
          {summary.on_hold ? 'On hold — choose a new date' : <>{longDate(summary.start_date)}{summary.departure && ` · ${summary.departure}`}</>}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Ref <span className="font-mono">{summary.booking_reference}</span> · {summary.payment_status_display}
        </p>
      </header>

      {summary.on_hold && <RescheduleCard summary={summary} token={token} onUpdated={setSummary} />}

      <section aria-labelledby="pay-title" className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 id="pay-title" className="text-lg font-bold text-gray-900">Payment</h2>
        <dl className="mt-3 grid grid-cols-3 gap-3 text-center">
          <div className="rounded-xl bg-gray-50 p-3"><dt className="text-xs text-gray-500">Total</dt><dd className="font-bold tabular-nums">{money(summary.total_amount)}</dd></div>
          <div className="rounded-xl bg-gray-50 p-3"><dt className="text-xs text-gray-500">Paid</dt><dd className="font-bold tabular-nums">{money(summary.amount_paid)}</dd></div>
          <div className={`rounded-xl p-3 ${balance > 0 ? 'bg-[#C8102E]/5' : 'bg-emerald-50'}`}>
            <dt className="text-xs text-gray-500">Balance</dt>
            <dd className={`font-bold tabular-nums ${balance > 0 ? 'text-[#C8102E]' : 'text-emerald-700'}`}>{money(balance)}</dd>
          </div>
        </dl>

        {summary.can_pay ? (
          <form className="mt-5 space-y-3" onSubmit={(e) => { e.preventDefault(); if (!amountError && amountValue > 0) setPayAmount(Number(amountValue.toFixed(2))); }}>
            {summary.balance_due_by && (
              <p className={`rounded-xl px-3 py-2 text-sm font-semibold ${summary.balance_overdue ? 'bg-[#C8102E]/10 text-[#C8102E]' : 'bg-amber-50 text-amber-900'}`}>
                {summary.balance_overdue ? 'Overdue — balance was due' : 'Balance due by'} {longDate(summary.balance_due_by)}
                <span className="mt-0.5 block text-xs font-normal">
                  {summary.balance_overdue
                    ? 'Please pay now: unpaid bookings are moved off their cruise 48 hours after the final notice (your payment is kept as credit).'
                    : 'If it isn\u2019t paid in time, the booking is moved off this cruise and your payment kept as credit for a new date.'}
                </span>
              </p>
            )}
            <p className="text-sm text-gray-600">Pay it all now or in instalments of {money(minimum)} or more — by card, EcoCash or Omari.</p>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => setAmount(balance.toFixed(2))}
                className={`rounded-full border px-4 py-2 text-sm font-semibold ${amountValue === balance ? 'border-[#C8102E] bg-[#C8102E]/5 text-[#C8102E]' : 'border-gray-300 text-gray-700'}`}>
                Full balance {money(balance)}
              </button>
              {balance / 2 >= minimum && (
                <button type="button" onClick={() => setAmount((balance / 2).toFixed(2))}
                  className={`rounded-full border px-4 py-2 text-sm font-semibold ${amountValue === Number((balance / 2).toFixed(2)) ? 'border-[#C8102E] bg-[#C8102E]/5 text-[#C8102E]' : 'border-gray-300 text-gray-700'}`}>
                  Half {money(balance / 2)}
                </button>
              )}
            </div>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-gray-700">Amount to pay now (USD)</span>
              <input type="number" inputMode="decimal" min={minimum} max={balance} step="0.01" value={amount}
                onChange={(e) => setAmount(e.target.value)} placeholder={balance.toFixed(2)}
                className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-lg tabular-nums focus:border-[#C8102E] focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20" />
            </label>
            {amountError && <p role="alert" className="text-sm text-[#C8102E]">{amountError}</p>}
            <button type="submit" disabled={!amount || Boolean(amountError)}
              className="w-full rounded-full bg-[#C8102E] px-5 py-3 font-bold text-white transition hover:bg-[#A00D24] disabled:opacity-50">
              {amount && !amountError ? `Pay ${money(amountValue)}` : 'Choose an amount'}
            </button>
          </form>
        ) : (
          <p className="mt-4 text-sm text-gray-600">
            {balance <= 0 ? '✅ Fully paid — thank you!' : summary.on_hold ? 'Choose a new date above, then pay the balance here.' : summary.trip_is_over ? 'This trip has taken place, so online payments are closed.' : 'Online payments are closed for this booking. Please message us on WhatsApp.'}
          </p>
        )}

        {summary.payments.length > 0 && (
          <details className="mt-4 text-sm">
            <summary className="cursor-pointer font-semibold text-gray-700">Payment history ({summary.payments.length})</summary>
            <ul className="mt-2 divide-y rounded-xl border">
              {summary.payments.map((p, i) => (
                <li key={i} className="flex items-center justify-between gap-3 px-3 py-2">
                  <span>{new Date(p.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })} · {p.method}</span>
                  <span className="whitespace-nowrap tabular-nums">{money(p.amount, p.currency)} <span className="text-gray-500">· {p.status_display}</span></span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <section aria-labelledby="ids-title" className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 id="ids-title" className="flex items-center gap-2 text-lg font-bold text-gray-900"><FaIdCard className="text-gray-400" aria-hidden /> Traveller IDs</h2>
        <p className="mt-1 text-sm text-gray-600">
          {missing.length
            ? `National parks need an ID or passport for everyone aged ${summary.id_required_from_age} and over. ${missing.length} still to go.`
            : 'All the IDs we need are in. Thank you!'}
        </p>
        <ul className="mt-4 space-y-3">
          {summary.travelers.map((t) => (
            <TravelerIdCard key={t.id} traveler={t} token={token} canUpload={summary.can_upload} onUpdated={setSummary} />
          ))}
        </ul>
        {unlisted > 0 && (
          <p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            {unlisted} of your {summary.passengers_booked} passengers {unlisted === 1 ? "isn't" : "aren't"} on the booking yet.{' '}
            <a className="font-semibold underline" target="_blank" rel="noopener noreferrer"
              href={whatsappLink(`Hi, I need to add passenger details to booking ${summary.booking_reference}.`)}>Send their details on WhatsApp</a>.
          </p>
        )}
      </section>

      <p className="flex items-center justify-center gap-2 text-center text-xs text-gray-500">
        <FaLock aria-hidden /> This page is private to your booking. Please don&apos;t share the link.
      </p>
      <p className="text-center text-sm">
        <Link href="/" className="font-semibold text-gray-600 hover:text-gray-900">Kalai Safaris home</Link>
      </p>
    </div>
  );
}

export default function ManageBookingPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  return (
    <main className="min-h-screen bg-[#FAF7F2] px-4 pb-16 pt-28">
      <Suspense fallback={null}>
        <ManageBookingContent token={decodeURIComponent(token)} />
      </Suspense>
    </main>
  );
}
