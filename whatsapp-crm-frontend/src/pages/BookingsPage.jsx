// src/pages/BookingsPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import {
  FiCalendar, FiChevronLeft, FiChevronRight, FiDownload, FiEdit2, FiMoreHorizontal, FiPlus, FiSearch, FiTrash2, FiUsers,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import ManifestExportPanel from '@/components/ManifestExportPanel';
import PassengerEditor from '@/components/PassengerEditor';
import PageHeader from '@/components/app/PageHeader';
import StatusBadge from '@/components/app/StatusBadge';
import CustomerPicker from '@/components/app/CustomerPicker';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { toursApi } from '@/lib/api';
import { apiErrorMessage, formatDate, formatDateTime, formatMoney, formatNumber, toIsoDate } from '@/lib/format';
import { ordersApi } from '@/services/orders';

const TABS = [
  { key: '', label: 'All' },
  { key: 'paid', label: 'Paid' },
  { key: 'deposit_paid', label: 'Deposit paid' },
  { key: 'awaiting_details', label: 'Awaiting details' },
  { key: 'pending', label: 'Pending payment' },
  { key: 'pending_manual', label: 'Manual verification' },
  { key: 'cancelled', label: 'Cancelled' },
];

// Paid / Deposit Paid are only accepted once every passenger is complete
// (server-enforced); "awaiting_details" is set automatically, never by hand.
const STATUS_OPTIONS = [
  ['pending', 'Pending payment'], ['pending_manual', 'Pending manual verification'], ['deposit_paid', 'Deposit paid'],
  ['paid', 'Paid in full'], ['refunded', 'Refunded'], ['cancelled', 'Cancelled'],
];
const SOURCE_OPTIONS = [['manual_entry', 'Manual entry'], ['phone_call', 'Phone call'], ['whatsapp', 'WhatsApp'], ['email_import', 'Email import']];

const EMPTY_FORM = {
  customer_id: null, customer_label: '', tour_id: '', tour_name: '', start_date: '', start_time: '', end_time: '', end_date: '',
  number_of_adults: 1, number_of_children: 0, total_amount: '', payment_status: 'pending', source: 'manual_entry', notes: '',
};

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';
const PAGE_SIZE = 50;
const SORTS = [
  ['-start_date', 'Tour date (latest first)'], ['start_date', 'Tour date (earliest first)'],
  ['-created_at', 'Booked (newest first)'], ['created_at', 'Booked (oldest first)'],
];
const PAYMENT_TONE = { successful: ['success', 'Received'], pending: ['warning', 'Awaiting verification'], failed: ['danger', 'Failed'], refunded: ['neutral', 'Refunded'] };

export default function BookingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const status = searchParams.get('status') || '';
  const tourFrom = searchParams.get('from') || '';
  const tourTo = searchParams.get('to') || '';
  const ordering = searchParams.get('sort') || '-start_date';
  const page = Math.max(1, Number(searchParams.get('page')) || 1);
  const [bookings, setBookings] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebounce(search, 300);
  const [tours, setTours] = useState([]);
  const [manifestDate, setManifestDate] = useState(() => toIsoDate(new Date()));
  const [rowBusy, setRowBusy] = useState(null);
  const [dialog, setDialog] = useState({ open: false, id: null });
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true);
    setError('');
    try {
      const res = await ordersApi.list({
        payment_status: status || undefined,
        search: debouncedSearch || undefined,
        start_date__gte: tourFrom || undefined,
        start_date__lte: tourTo || undefined,
        ordering,
        page,
        page_size: PAGE_SIZE,
      });
      const list = res.data.results || res.data || [];
      setBookings(list);
      setCount(res.data.count ?? list.length);
      return list;
    } catch (err) {
      setError(apiErrorMessage(err));
      return [];
    } finally {
      setLoading(false);
    }
  }, [status, debouncedSearch, tourFrom, tourTo, ordering, page]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    toursApi.list().then((res) => setTours(res.data.tours || [])).catch(() => setTours([]));
  }, []);

  const updateParams = (changes) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!('page' in changes)) next.delete('page');
    setSearchParams(next, { replace: true });
  };
  const setStatus = (key) => updateParams({ status: key });
  // A new search starts from page 1.
  useEffect(() => {
    if (page !== 1 && debouncedSearch) updateParams({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);
  const pages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  const filtered = Boolean(status || search || tourFrom || tourTo);

  const editingBooking = bookings.find((b) => b.id === dialog.id);

  const openNew = () => {
    setForm({ ...EMPTY_FORM, start_date: toIsoDate(new Date()), end_date: toIsoDate(new Date()) });
    setFormError('');
    setDialog({ open: true, id: null });
  };

  const openEdit = (b) => {
    setForm({
      customer_id: b.customer?.contact_id ?? null,
      customer_label: b.customer?.full_name || '',
      tour_id: b.tour?.id ? String(b.tour.id) : '',
      tour_name: b.tour_name || '',
      start_date: b.start_date || '', start_time: (b.start_time || '').slice(0, 5), end_time: (b.end_time || '').slice(0, 5), end_date: b.end_date || '',
      number_of_adults: b.number_of_adults ?? 1, number_of_children: b.number_of_children ?? 0,
      total_amount: b.total_amount || '', payment_status: b.payment_status || 'pending',
      source: b.source || 'manual_entry', notes: b.notes || '',
    });
    setFormError('');
    setDialog({ open: true, id: b.id });
  };

  const totalFor = (tour, adults, children) => {
    const adultPrice = Number(tour.price_per_adult || tour.base_price || 0);
    const childPrice = Number(tour.price_per_child ?? adultPrice);
    return (adultPrice * Number(adults || 0) + childPrice * Number(children || 0)).toFixed(2);
  };

  const set = (field) => (e) => {
    const { value } = e.target;
    setForm((f) => {
      const next = { ...f, [field]: value };
      // Keep a catalogue tour's price in step with the passenger count.
      const tour = tours.find((t) => String(t.id) === f.tour_id);
      if (tour && (field === 'number_of_adults' || field === 'number_of_children')) {
        next.total_amount = totalFor(tour, next.number_of_adults, next.number_of_children);
      }
      return next;
    });
  };

  // Picking a catalogue tour fills in its name, duration and price.
  const chooseTour = (e) => {
    const tour = tours.find((t) => String(t.id) === e.target.value);
    setForm((f) => {
      const next = { ...f, tour_id: e.target.value };
      if (!tour) return next;
      next.tour_name = tour.name;
      if (f.start_date && tour.duration_days) {
        const end = new Date(`${f.start_date}T00:00:00`);
        end.setDate(end.getDate() + Math.max(tour.duration_days - 1, 0));
        next.end_date = toIsoDate(end);
      }
      next.total_amount = totalFor(tour, f.number_of_adults, f.number_of_children);
      return next;
    });
  };

  const save = async (e) => {
    e.preventDefault();
    if (form.end_date < form.start_date) {
      setFormError('The end date is before the start date.');
      return;
    }
    setSaving(true);
    setFormError('');
    const payload = {
      customer_id: form.customer_id,
      tour_id: form.tour_id ? Number(form.tour_id) : null,
      tour_name: form.tour_name.trim(),
      start_date: form.start_date, start_time: form.start_time || null, end_time: (form.start_time && form.end_time) || null, end_date: form.end_date,
      number_of_adults: Number(form.number_of_adults || 0),
      number_of_children: Number(form.number_of_children || 0),
      total_amount: form.total_amount === '' ? '0.00' : form.total_amount,
      payment_status: form.payment_status,
      source: form.source,
      notes: form.notes,
    };
    try {
      if (dialog.id) {
        await ordersApi.update(dialog.id, payload);
        toast.success('Booking saved');
        setDialog({ open: false, id: null });
      } else {
        const res = await ordersApi.create(payload);
        toast.success('Booking created — now add its passengers');
        setBookings((list) => [res.data, ...list.filter((b) => b.id !== res.data.id)]);
        // Stay in the dialog so passengers can be added straight away.
        setDialog({ open: true, id: res.data.id });
      }
      load({ quiet: true });
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (b) => {
    if (!window.confirm(`Delete booking ${b.booking_reference}? Its passengers are deleted too. This can't be undone.`)) return;
    try {
      await ordersApi.delete(b.id);
      toast.success('Booking deleted');
      load({ quiet: true });
    } catch {
      // Interceptor shows the error.
    }
  };

  const downloadManifest = async (b) => {
    setManifestDate(b.start_date);
    setRowBusy(b.id);
    try {
      await ordersApi.downloadManifest('park', b.start_date, 'pdf');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRowBusy(null);
    }
  };

  // Passenger changes can confirm or hold the booking server-side: refresh the
  // table and keep the open form's status in sync so a stale value isn't re-sent.
  const handlePassengersChanged = async () => {
    const list = await load({ quiet: true });
    const updated = list.find((b) => b.id === dialog.id);
    if (updated) setForm((f) => ({ ...f, payment_status: updated.payment_status }));
  };

  return (
    <>
      <PageHeader
        title="Bookings"
        description="Every tour booking, its payment status and passenger list."
        actions={<Button onClick={openNew}><FiPlus /> New booking</Button>}
      />

      <ManifestExportPanel date={manifestDate} onDateChange={setManifestDate} />

      <div className="mb-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1 xl:pb-0" role="tablist" aria-label="Filter by status">
          {TABS.map((t) => (
            <Button key={t.key || 'all'} role="tab" aria-selected={status === t.key} size="sm" className="shrink-0"
              variant={status === t.key ? 'secondary' : 'ghost'} onClick={() => setStatus(t.key)}>
              {t.label}
            </Button>
          ))}
        </div>
        <div className="relative w-full xl:w-72">
          <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search reference, tour, customer…" className="pl-9" aria-label="Search bookings" />
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-2">
        <div>
          <Label htmlFor="bf-from" className="mb-1 text-xs text-muted-foreground">Tour date from</Label>
          <Input id="bf-from" type="date" className="w-40" value={tourFrom} max={tourTo || undefined} onChange={(e) => updateParams({ from: e.target.value })} />
        </div>
        <div>
          <Label htmlFor="bf-to" className="mb-1 text-xs text-muted-foreground">to</Label>
          <Input id="bf-to" type="date" className="w-40" value={tourTo} min={tourFrom || undefined} onChange={(e) => updateParams({ to: e.target.value })} />
        </div>
        <Button size="sm" variant={tourFrom === toIsoDate(new Date()) && !tourTo ? 'secondary' : 'outline'}
          onClick={() => updateParams({ from: toIsoDate(new Date()), to: '', sort: 'start_date' })}>Upcoming</Button>
        {(tourFrom || tourTo) && <Button size="sm" variant="ghost" onClick={() => updateParams({ from: '', to: '' })}>Clear dates</Button>}
        <div className="ml-auto">
          <Label htmlFor="bf-sort" className="mb-1 text-xs text-muted-foreground">Sort by</Label>
          <select id="bf-sort" className={`${selectClass} w-56`} value={ordering} onChange={(e) => updateParams({ sort: e.target.value === '-start_date' ? '' : e.target.value })}>
            {SORTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={() => load()} /> : loading ? <TableSkeleton rows={6} cols={6} /> : bookings.length === 0 ? (
          <EmptyState
            icon={FiCalendar}
            title={filtered ? 'No bookings match' : 'No bookings yet'}
            description={filtered ? 'Try another status, date range or search.' : 'Bookings from WhatsApp, the website and staff appear here.'}
            action={!filtered ? <Button onClick={openNew}><FiPlus /> New booking</Button> : null}
          />
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Booking</th>
                  <th className="px-4 py-3 font-medium">Tour</th>
                  <th className="px-4 py-3 font-medium">Tour date</th>
                  <th className="px-4 py-3 font-medium">Booked</th>
                  <th className="px-4 py-3 font-medium">Passengers</th>
                  <th className="px-4 py-3 text-right font-medium">Paid / total</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {bookings.map((b) => {
                  const pax = (b.number_of_adults || 0) + (b.number_of_children || 0);
                  // Missing details only block paid bookings; elsewhere it's informational.
                  const incomplete = (b.traveler_details_problems || []).length > 0
                    && ['paid', 'deposit_paid', 'awaiting_details'].includes(b.payment_status);
                  return (
                    <tr key={b.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <button type="button" className="text-left font-medium hover:underline" onClick={() => openEdit(b)}>
                          {b.customer?.full_name || 'No customer'}
                        </button>
                        <span className="block whitespace-nowrap font-mono text-xs text-muted-foreground">{b.booking_reference}</span>
                      </td>
                      <td className="px-4 py-3">{b.tour_name}</td>
                      <td className="whitespace-nowrap px-4 py-3">
                        {formatDate(b.start_date)}
                        {b.start_time && <span className="ml-1.5 text-xs tabular-nums text-muted-foreground">{b.start_time.slice(0, 5)}{b.end_time ? `–${b.end_time.slice(0, 5)}` : ''}</span>}
                        {b.end_date && b.end_date !== b.start_date && <span className="block text-xs text-muted-foreground">to {formatDate(b.end_date)}</span>}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3" title={formatDateTime(b.created_at)}>
                        {formatDate(b.created_at)}
                        <span className="block text-xs text-muted-foreground">{b.source_display}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-1.5">
                          <FiUsers className="size-3.5 text-muted-foreground" aria-hidden />
                          {b.number_of_adults || 0} adult{b.number_of_adults === 1 ? '' : 's'}{b.number_of_children ? `, ${b.number_of_children} child${b.number_of_children === 1 ? '' : 'ren'}` : ''}
                        </span>
                        <span className={`text-xs ${incomplete ? 'text-warning' : 'text-muted-foreground'}`} title={(b.traveler_details_problems || []).join(' ')}>
                          {b.traveler_count ?? 0} of {pax} with details
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums">
                        {formatMoney(b.amount_paid)} <span className="text-muted-foreground">/ {formatMoney(b.total_amount)}</span>
                        {(b.payments || []).length > 0 && (
                          <span className="block text-xs text-muted-foreground">
                            {b.payments.length} payment{b.payments.length === 1 ? '' : 's'}
                            {b.payments.some((p) => p.status === 'pending') && <span className="text-warning"> · to verify</span>}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={b.payment_status} /></td>
                      <td className="px-4 py-3 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label={`Actions for ${b.booking_reference}`}><FiMoreHorizontal /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEdit(b)}><FiEdit2 className="size-4" /> Edit & passengers</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => downloadManifest(b)} disabled={rowBusy === b.id}>
                              <FiDownload className="size-4" /> Park manifest for {formatDate(b.start_date, 'd MMM')}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => remove(b)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !error && bookings.length > 0 && (
          <div className="flex items-center justify-between gap-3 border-t px-4 py-2.5 text-xs text-muted-foreground">
            <span>
              {formatNumber((page - 1) * PAGE_SIZE + 1)}–{formatNumber((page - 1) * PAGE_SIZE + bookings.length)} of {formatNumber(count)} booking{count === 1 ? '' : 's'}
            </span>
            <span className="flex items-center gap-1">
              <Button size="icon" variant="ghost" aria-label="Previous page" disabled={page <= 1} onClick={() => updateParams({ page: String(page - 1) })}><FiChevronLeft /></Button>
              Page {page} of {pages}
              <Button size="icon" variant="ghost" aria-label="Next page" disabled={page >= pages} onClick={() => updateParams({ page: String(page + 1) })}><FiChevronRight /></Button>
            </span>
          </div>
        )}
      </div>

      <Dialog open={dialog.open} onOpenChange={(open) => setDialog((d) => ({ ...d, open }))}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          <form onSubmit={save} className="space-y-4">
            <DialogHeader>
              <DialogTitle>{dialog.id ? `Booking ${editingBooking?.booking_reference || ''}` : 'New booking'}</DialogTitle>
              <DialogDescription>
                {dialog.id ? 'Update the booking and manage its passengers below.' : 'Create the booking first, then add its passengers.'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label htmlFor="b-customer" className="mb-1.5">Customer</Label>
                <CustomerPicker id="b-customer" value={form.customer_id} initialLabel={form.customer_label}
                  onChange={(id, label) => setForm((f) => ({ ...f, customer_id: id, customer_label: label || '' }))} />
              </div>
              <div>
                <Label htmlFor="b-tour" className="mb-1.5">Tour</Label>
                <select id="b-tour" className={selectClass} value={form.tour_id} onChange={chooseTour}>
                  <option value="">Custom / not in catalogue</option>
                  {tours.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div>
                <Label htmlFor="b-tour-name" className="mb-1.5">Tour name</Label>
                <Input id="b-tour-name" value={form.tour_name} onChange={set('tour_name')} required />
              </div>
              <div>
                <Label htmlFor="b-start" className="mb-1.5">Start date</Label>
                <Input id="b-start" type="date" value={form.start_date} onChange={set('start_date')} required />
              </div>
              <div>
                <Label htmlFor="b-time" className="mb-1.5">Time slot <span className="font-normal text-muted-foreground">(optional)</span></Label>
                <div className="flex items-center gap-2">
                  <Input id="b-time" type="time" aria-label="Slot start" value={form.start_time} onChange={set('start_time')} />
                  <span className="text-muted-foreground">–</span>
                  <Input type="time" aria-label="Slot end" value={form.end_time} min={form.start_time} disabled={!form.start_time} onChange={set('end_time')} />
                </div>
              </div>
              <div>
                <Label htmlFor="b-end" className="mb-1.5">End date</Label>
                <Input id="b-end" type="date" value={form.end_date} min={form.start_date} onChange={set('end_date')} required />
              </div>
              <div>
                <Label htmlFor="b-adults" className="mb-1.5">Adults</Label>
                <Input id="b-adults" type="number" min="0" value={form.number_of_adults} onChange={set('number_of_adults')} required />
              </div>
              <div>
                <Label htmlFor="b-children" className="mb-1.5">Children</Label>
                <Input id="b-children" type="number" min="0" value={form.number_of_children} onChange={set('number_of_children')} required />
              </div>
              <div>
                <Label htmlFor="b-total" className="mb-1.5">Total amount (USD)</Label>
                <Input id="b-total" type="number" min="0" step="0.01" value={form.total_amount} onChange={set('total_amount')} required />
              </div>
              <div>
                <Label htmlFor="b-status" className="mb-1.5">Payment status</Label>
                <select id="b-status" className={selectClass} value={form.payment_status} onChange={set('payment_status')}>
                  {form.payment_status === 'awaiting_details' && <option value="awaiting_details" disabled>Paid — awaiting passenger details (automatic)</option>}
                  {STATUS_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
                <p className="mt-1 text-xs text-muted-foreground">Paid and Deposit paid need complete details for every passenger.</p>
              </div>
              <div>
                <Label htmlFor="b-source" className="mb-1.5">Source</Label>
                <select id="b-source" className={selectClass} value={form.source} onChange={set('source')}>
                  {SOURCE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="b-notes" className="mb-1.5">Internal notes</Label>
                <Textarea id="b-notes" rows={2} value={form.notes} onChange={set('notes')} />
              </div>
            </div>
            {formError && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{formError}</p>}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setDialog({ open: false, id: null })}>Close</Button>
              <Button type="submit" disabled={saving}>{saving ? 'Saving…' : dialog.id ? 'Save booking' : 'Create booking'}</Button>
            </div>
          </form>
          {dialog.id && editingBooking && (
            <section className="space-y-2 border-t pt-4" aria-labelledby="b-payments-title">
              <div className="flex items-baseline justify-between gap-3">
                <h3 id="b-payments-title" className="font-semibold">Payments</h3>
                <span className="text-xs text-muted-foreground">
                  Booked {formatDateTime(editingBooking.created_at)} · {editingBooking.source_display} · updated {formatDateTime(editingBooking.updated_at)}
                </span>
              </div>
              {(editingBooking.payments || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No payments recorded yet.</p>
              ) : (
                <ul className="divide-y rounded-md border text-sm">
                  {editingBooking.payments.map((p) => {
                    const [tone, label] = PAYMENT_TONE[p.status] || ['neutral', p.payment_status_display];
                    return (
                      <li key={p.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2">
                        <span className="w-36 tabular-nums">{formatDateTime(p.created_at)}</span>
                        <span className="min-w-0 flex-1">
                          {p.payment_method_display}
                          {p.transaction_reference && <span className="block truncate font-mono text-xs text-muted-foreground">{p.transaction_reference}</span>}
                        </span>
                        <span className="font-medium tabular-nums">{formatMoney(p.amount, p.currency)}</span>
                        <StatusBadge status={p.status} tone={tone} label={label} />
                      </li>
                    );
                  })}
                </ul>
              )}
              {(editingBooking.payments || []).some((p) => p.status === 'pending') && (
                <p className="text-xs text-muted-foreground">
                  Verify pending payments on the <Link className="text-primary underline" to={`/payments?status=pending&q=${encodeURIComponent(editingBooking.booking_reference)}`}>Payments page</Link>.
                </p>
              )}
            </section>
          )}
          {dialog.id && editingBooking && (
            <PassengerEditor booking={editingBooking} onChanged={handlePassengersChanged} />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
