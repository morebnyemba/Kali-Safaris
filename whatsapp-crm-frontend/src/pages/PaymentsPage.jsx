// src/pages/PaymentsPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import {
  FiAlertCircle, FiCheck, FiChevronLeft, FiChevronRight, FiClock, FiCreditCard, FiDollarSign, FiDownload, FiSearch, FiX,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import PageHeader from '@/components/app/PageHeader';
import StatCard from '@/components/app/StatCard';
import StatusBadge from '@/components/app/StatusBadge';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { useAuth } from '@/context/AuthContext';
import { APP_ROLES, getRoleFromUser } from '@/lib/rbac';
import { apiErrorMessage, formatDate, formatDateTime, formatMoney, formatNumber, toIsoDate } from '@/lib/format';
import { PAYMENT_METHODS, paymentsApi } from '@/services/payments';

const PAGE_SIZE = 50;

const TABS = [
  { key: '', label: 'All' },
  { key: 'successful', label: 'Received' },
  { key: 'pending', label: 'Awaiting verification' },
  { key: 'failed', label: 'Failed / rejected' },
  { key: 'refunded', label: 'Refunded' },
];

// Payment statuses differ from booking statuses: label them for finance.
const PAYMENT_STATUS = {
  successful: ['success', 'Received'],
  pending: ['warning', 'Awaiting verification'],
  failed: ['danger', 'Failed'],
  refunded: ['neutral', 'Refunded'],
};

const daysAgo = (n) => { const d = new Date(); d.setDate(d.getDate() - n); return toIsoDate(d); };
const PRESETS = [
  { label: 'Today', from: () => toIsoDate(new Date()), to: () => toIsoDate(new Date()) },
  { label: 'Last 7 days', from: () => daysAgo(6), to: () => toIsoDate(new Date()) },
  { label: 'This month', from: () => { const d = new Date(); return toIsoDate(new Date(d.getFullYear(), d.getMonth(), 1)); }, to: () => toIsoDate(new Date()) },
  { label: 'All time', from: () => '', to: () => '' },
];

const selectClass = 'h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

/** "$1,200.00 + ZWG 50.00" — totals are per currency, never summed across. */
const moneyByCurrency = (totals) => {
  const entries = Object.entries(totals || {});
  if (!entries.length) return formatMoney(0);
  return entries.map(([cur, amount]) => formatMoney(amount, cur)).join(' + ');
};

const csvCell = (v) => {
  const s = v == null ? '' : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export default function PaymentsPage() {
  const { user } = useAuth();
  const canReview = getRoleFromUser(user) !== APP_ROLES.AGENT;
  const [params, setParams] = useSearchParams();
  const status = params.get('status') || '';
  const method = params.get('method') || '';
  const dateFrom = params.get('from') || '';
  const dateTo = params.get('to') || '';
  const page = Math.max(1, Number(params.get('page')) || 1);
  const [search, setSearch] = useState(params.get('q') || '');
  const [debouncedSearch] = useDebounce(search, 300);

  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [detail, setDetail] = useState(null);
  const [rejecting, setRejecting] = useState(null);
  const [reason, setReason] = useState('');

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!('page' in changes)) next.delete('page');
    setParams(next, { replace: true });
  };

  useEffect(() => {
    if ((params.get('q') || '') !== debouncedSearch) update({ q: debouncedSearch });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const filters = useCallback(() => ({
    status: status || undefined,
    payment_method: method || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    search: debouncedSearch || undefined,
  }), [status, method, dateFrom, dateTo, debouncedSearch]);

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true);
    setError('');
    try {
      const f = filters();
      // Summary ignores the status tab so the tiles always show the full picture.
      const [list, sum] = await Promise.all([
        paymentsApi.list({ ...f, page, page_size: PAGE_SIZE, ordering: '-created_at' }),
        paymentsApi.summary({ ...f, status: undefined }),
      ]);
      setRows(list.data.results || []);
      setCount(list.data.count ?? 0);
      setSummary(sum.data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => { load(); }, [load]);

  const approve = async (p) => {
    if (!window.confirm(`Approve ${formatMoney(p.amount, p.currency)} for ${p.booking_reference || 'this payment'}? The customer is notified on WhatsApp.`)) return;
    setBusyId(p.id);
    try {
      await paymentsApi.approve(p.id);
      toast.success('Payment approved — booking updated');
      window.dispatchEvent(new Event('nav-counts:refresh'));
      setDetail(null);
      load({ quiet: true });
    } catch {
      // Interceptor shows the error.
    } finally {
      setBusyId(null);
    }
  };

  const submitReject = async (e) => {
    e.preventDefault();
    const p = rejecting;
    setBusyId(p.id);
    try {
      await paymentsApi.reject(p.id, reason.trim());
      toast.success('Payment rejected — customer notified');
      window.dispatchEvent(new Event('nav-counts:refresh'));
      setRejecting(null);
      setDetail(null);
      load({ quiet: true });
    } catch {
      // Interceptor shows the error.
    } finally {
      setBusyId(null);
    }
  };

  const exportCsv = async () => {
    setExporting(true);
    try {
      const all = [];
      for (let p = 1; p <= 50; p += 1) {
        const res = await paymentsApi.list({ ...filters(), page: p, page_size: 100, ordering: '-created_at' });
        all.push(...(res.data.results || []));
        if (!res.data.next) break;
      }
      const header = ['Date', 'Booking', 'Customer', 'Tour', 'Tour date', 'Method', 'Reference', 'Currency', 'Amount', 'Status', 'Notes'];
      const lines = all.map((p) => [
        formatDateTime(p.created_at), p.booking_reference, p.customer_name, p.tour_name, p.tour_date,
        p.payment_method_display, p.transaction_reference, p.currency, p.amount, p.payment_status_display, p.notes,
      ].map(csvCell).join(','));
      const blob = new Blob([[header.join(','), ...lines].join('\n')], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `payments_${dateFrom || 'all'}_${dateTo || toIsoDate(new Date())}.csv`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast.success(`Exported ${all.length} payment${all.length === 1 ? '' : 's'}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setExporting(false);
    }
  };

  const bs = summary?.by_status || {};
  const pages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  const filtered = Boolean(status || method || dateFrom || dateTo || debouncedSearch);
  const activePreset = PRESETS.find((p) => p.from() === dateFrom && p.to() === dateTo);

  const statusBadge = (s) => {
    const [tone, label] = PAYMENT_STATUS[s] || ['neutral', s];
    return <StatusBadge status={s} tone={tone} label={label} />;
  };

  return (
    <>
      <PageHeader
        title="Payments"
        description="Every payment from the website, WhatsApp and staff — card, EcoCash, Omari, Paynow and bank transfer."
        actions={<Button variant="outline" onClick={exportCsv} disabled={exporting || count === 0}><FiDownload /> {exporting ? 'Exporting…' : 'Export CSV'}</Button>}
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard label="Received" icon={FiDollarSign} loading={!summary}
          value={moneyByCurrency(bs.successful?.totals)} hint={`${formatNumber(bs.successful?.count || 0)} payments`} />
        <StatCard label="Awaiting verification" icon={FiClock} tone="warning" loading={!summary}
          value={formatNumber(bs.pending?.count || 0)} hint={bs.pending ? moneyByCurrency(bs.pending.totals) : 'Nothing to review'} />
        <StatCard label="Failed / rejected" icon={FiAlertCircle} tone="danger" loading={!summary}
          value={formatNumber(bs.failed?.count || 0)} hint={bs.failed ? moneyByCurrency(bs.failed.totals) : '—'} />
      </div>

      {summary?.by_method?.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2" aria-label="Received by method">
          {summary.by_method.map((m) => (
            <span key={`${m.payment_method}-${m.currency}`} className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs">
              <FiCreditCard className="size-3.5 text-muted-foreground" aria-hidden />
              {m.label}: <strong className="tabular-nums">{formatMoney(m.total, m.currency)}</strong>
              <span className="text-muted-foreground">({m.count})</span>
            </span>
          ))}
        </div>
      )}

      <div className="mb-3 -mx-1 flex gap-1 overflow-x-auto px-1 pb-1" role="tablist" aria-label="Filter by status">
        {TABS.map((t) => (
          <Button key={t.key || 'all'} role="tab" aria-selected={status === t.key} size="sm" className="shrink-0"
            variant={status === t.key ? 'secondary' : 'ghost'} onClick={() => update({ status: t.key })}>
            {t.label}
            {t.key === 'pending' && bs.pending?.count > 0 && (
              <span className="ml-1 rounded-full bg-warning/20 px-1.5 text-xs tabular-nums">{bs.pending.count}</span>
            )}
          </Button>
        ))}
      </div>

      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-end">
        <div className="flex flex-wrap gap-1">
          {PRESETS.map((p) => (
            <Button key={p.label} size="sm" variant={activePreset === p ? 'secondary' : 'outline'}
              onClick={() => update({ from: p.from(), to: p.to() })}>
              {p.label}
            </Button>
          ))}
        </div>
        <div className="flex items-end gap-2">
          <div>
            <Label htmlFor="p-from" className="mb-1 text-xs text-muted-foreground">From</Label>
            <Input id="p-from" type="date" value={dateFrom} max={dateTo || undefined} onChange={(e) => update({ from: e.target.value })} className="w-40" />
          </div>
          <div>
            <Label htmlFor="p-to" className="mb-1 text-xs text-muted-foreground">To</Label>
            <Input id="p-to" type="date" value={dateTo} min={dateFrom || undefined} onChange={(e) => update({ to: e.target.value })} className="w-40" />
          </div>
        </div>
        <select aria-label="Payment method" className={selectClass} value={method} onChange={(e) => update({ method: e.target.value })}>
          <option value="">All methods</option>
          {PAYMENT_METHODS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <div className="relative w-full lg:ml-auto lg:w-72">
          <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Reference, booking, customer, tour…" className="pl-9" aria-label="Search payments" />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={() => load()} /> : loading ? <TableSkeleton rows={8} cols={7} /> : rows.length === 0 ? (
          <EmptyState icon={FiCreditCard}
            title={filtered ? 'No payments match' : 'No payments yet'}
            description={filtered ? 'Try another date range, method or search.' : 'Payments from every channel appear here as they arrive.'} />
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full min-w-[960px] text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Customer / booking</th>
                  <th className="px-4 py-3 font-medium">Tour</th>
                  <th className="px-4 py-3 font-medium">Method</th>
                  <th className="px-4 py-3 font-medium">Reference</th>
                  <th className="px-4 py-3 text-right font-medium">Amount</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {rows.map((p) => (
                  <tr key={p.id} className="hover:bg-muted/30">
                    <td className="whitespace-nowrap px-4 py-3">
                      <button type="button" className="text-left hover:underline" onClick={() => setDetail(p)}>
                        {formatDate(p.created_at)}
                        <span className="block text-xs tabular-nums text-muted-foreground">{formatDate(p.created_at, 'HH:mm')}</span>
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium">{p.customer_name || 'No customer'}</span>
                      <span className="block whitespace-nowrap font-mono text-xs text-muted-foreground">{p.booking_reference || '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      {p.tour_name || '—'}
                      {p.tour_date && <span className="block text-xs text-muted-foreground">{formatDate(p.tour_date)}</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{p.payment_method_display}</td>
                    <td className="max-w-[180px] truncate px-4 py-3 font-mono text-xs" title={p.transaction_reference || ''}>{p.transaction_reference || '—'}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-right font-medium tabular-nums">{formatMoney(p.amount, p.currency)}</td>
                    <td className="px-4 py-3">{statusBadge(p.status)}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      {p.status === 'pending' && canReview ? (
                        <span className="inline-flex gap-1">
                          <Button size="sm" variant="outline" disabled={busyId === p.id} onClick={() => approve(p)} aria-label={`Approve payment ${p.booking_reference || ''}`}>
                            <FiCheck /> Approve
                          </Button>
                          <Button size="sm" variant="ghost" disabled={busyId === p.id} onClick={() => { setReason(''); setRejecting(p); }} aria-label={`Reject payment ${p.booking_reference || ''}`}>
                            <FiX />
                          </Button>
                        </span>
                      ) : (
                        <Button size="sm" variant="ghost" onClick={() => setDetail(p)}>Details</Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !error && count > 0 && (
          <div className="flex items-center justify-between gap-3 border-t px-4 py-2.5 text-xs text-muted-foreground">
            <span>
              {formatNumber((page - 1) * PAGE_SIZE + 1)}–{formatNumber(Math.min(page * PAGE_SIZE, count))} of {formatNumber(count)} payment{count === 1 ? '' : 's'}
            </span>
            <span className="flex items-center gap-1">
              <Button size="icon" variant="ghost" aria-label="Previous page" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}><FiChevronLeft /></Button>
              Page {page} of {pages}
              <Button size="icon" variant="ghost" aria-label="Next page" disabled={page >= pages} onClick={() => update({ page: String(page + 1) })}><FiChevronRight /></Button>
            </span>
          </div>
        )}
      </div>

      <Dialog open={Boolean(detail)} onOpenChange={(open) => !open && setDetail(null)}>
        <DialogContent className="sm:max-w-lg">
          {detail && (
            <>
              <DialogHeader>
                <DialogTitle>{formatMoney(detail.amount, detail.currency)} · {detail.payment_method_display}</DialogTitle>
                <DialogDescription>{statusBadge(detail.status)}</DialogDescription>
              </DialogHeader>
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
                <dt className="text-muted-foreground">Received</dt><dd>{formatDateTime(detail.created_at)}</dd>
                <dt className="text-muted-foreground">Last updated</dt><dd>{formatDateTime(detail.updated_at)}</dd>
                <dt className="text-muted-foreground">Customer</dt><dd>{detail.customer_name || '—'}</dd>
                <dt className="text-muted-foreground">Booking</dt><dd className="font-mono text-xs leading-5">{detail.booking_reference || '—'}</dd>
                <dt className="text-muted-foreground">Tour</dt><dd>{detail.tour_name || '—'}{detail.tour_date ? ` · ${formatDate(detail.tour_date)}` : ''}</dd>
                <dt className="text-muted-foreground">Reference</dt><dd className="break-all font-mono text-xs leading-5">{detail.transaction_reference || '—'}</dd>
                <dt className="text-muted-foreground">Payment ID</dt><dd className="break-all font-mono text-xs leading-5">{detail.id}</dd>
              </dl>
              {detail.notes && (
                <div>
                  <p className="mb-1 text-sm text-muted-foreground">Notes</p>
                  <p className="whitespace-pre-wrap rounded-md bg-muted/50 p-3 text-sm">{detail.notes}</p>
                </div>
              )}
              {detail.status === 'pending' && canReview && (
                <div className="flex justify-end gap-2">
                  <Button variant="outline" disabled={busyId === detail.id} onClick={() => { setReason(''); setRejecting(detail); }}>Reject</Button>
                  <Button disabled={busyId === detail.id} onClick={() => approve(detail)}><FiCheck /> Approve</Button>
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(rejecting)} onOpenChange={(open) => !open && setRejecting(null)}>
        <DialogContent className="sm:max-w-md">
          <form onSubmit={submitReject} className="space-y-4">
            <DialogHeader>
              <DialogTitle>Reject payment</DialogTitle>
              <DialogDescription>
                {rejecting && `${formatMoney(rejecting.amount, rejecting.currency)} for ${rejecting.booking_reference || 'this booking'}.`} The customer is told on WhatsApp.
              </DialogDescription>
            </DialogHeader>
            <div>
              <Label htmlFor="p-reason" className="mb-1.5">Reason <span className="font-normal text-muted-foreground">(sent to the customer)</span></Label>
              <Textarea id="p-reason" rows={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Amount not received in our account" />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setRejecting(null)}>Cancel</Button>
              <Button type="submit" variant="destructive" disabled={busyId === rejecting?.id}>Reject payment</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
