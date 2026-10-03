// src/pages/InquiriesPage.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import { FiClipboard, FiEdit2, FiMoreHorizontal, FiPlus, FiSearch, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import PageHeader from '@/components/app/PageHeader';
import StatusBadge from '@/components/app/StatusBadge';
import CustomerPicker from '@/components/app/CustomerPicker';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { inquiriesApi } from '@/lib/api';
import { apiErrorMessage, formatDate } from '@/lib/format';

const STATUSES = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'proposal_sent', label: 'Proposal sent' },
  { value: 'converted', label: 'Converted' },
  { value: 'closed', label: 'Closed' },
];

const EMPTY_FORM = {
  customer_id: null, customer_label: '', lead_traveler_name: '', destinations: '', preferred_dates: '',
  number_of_travelers: '', status: 'new', notes: '',
};

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

export default function InquiriesPage() {
  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebounce(search, 300);
  const [dialog, setDialog] = useState({ open: false, id: null });
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await inquiriesApi.list({ page_size: 100, search: debouncedSearch || undefined });
      setInquiries(res.data.results || res.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch]);

  useEffect(() => { load(); }, [load]);

  const counts = useMemo(() => {
    const c = { all: inquiries.length };
    STATUSES.forEach((s) => { c[s.value] = inquiries.filter((i) => i.status === s.value).length; });
    return c;
  }, [inquiries]);

  const visible = statusFilter === 'all' ? inquiries : inquiries.filter((i) => i.status === statusFilter);

  const openNew = () => {
    setForm(EMPTY_FORM);
    setFormError('');
    setDialog({ open: true, id: null });
  };

  const openEdit = (inq) => {
    setForm({
      customer_id: inq.customer?.contact_id ?? null,
      customer_label: inq.customer?.full_name || '',
      lead_traveler_name: inq.lead_traveler_name || '',
      destinations: inq.destinations || '',
      preferred_dates: inq.preferred_dates || '',
      number_of_travelers: inq.number_of_travelers ?? '',
      status: inq.status || 'new',
      notes: inq.notes || '',
    });
    setFormError('');
    setDialog({ open: true, id: inq.id });
  };

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const save = async (e) => {
    e.preventDefault();
    if (!form.customer_id) {
      setFormError('Choose the customer this inquiry belongs to.');
      return;
    }
    setSaving(true);
    setFormError('');
    const payload = {
      customer_id: form.customer_id,
      lead_traveler_name: form.lead_traveler_name.trim(),
      destinations: form.destinations.trim(),
      preferred_dates: form.preferred_dates.trim(),
      number_of_travelers: form.number_of_travelers === '' ? null : Number(form.number_of_travelers),
      status: form.status,
      notes: form.notes,
    };
    try {
      if (dialog.id) {
        await inquiriesApi.update(dialog.id, payload);
        toast.success('Inquiry updated');
      } else {
        await inquiriesApi.create(payload);
        toast.success('Inquiry created');
      }
      setDialog({ open: false, id: null });
      load();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (inq, status) => {
    const previous = inq.status;
    setInquiries((list) => list.map((i) => (i.id === inq.id ? { ...i, status } : i)));
    try {
      await inquiriesApi.update(inq.id, { status });
    } catch (err) {
      setInquiries((list) => list.map((i) => (i.id === inq.id ? { ...i, status: previous } : i)));
      toast.error(apiErrorMessage(err));
    }
  };

  const remove = async (inq) => {
    if (!window.confirm(`Delete inquiry ${inq.inquiry_reference || ''}? This can't be undone.`)) return;
    try {
      await inquiriesApi.delete(inq.id);
      toast.success('Inquiry deleted');
      load();
    } catch {
      // Interceptor shows the error.
    }
  };

  return (
    <>
      <PageHeader
        title="Tour inquiries"
        description="Custom tour requests from WhatsApp and staff. Move each one through to a proposal or booking."
        actions={<Button onClick={openNew}><FiPlus /> New inquiry</Button>}
      />

      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filter by status">
          {[{ value: 'all', label: 'All' }, ...STATUSES].map((s) => (
            <Button
              key={s.value}
              role="tab"
              aria-selected={statusFilter === s.value}
              size="sm"
              variant={statusFilter === s.value ? 'secondary' : 'ghost'}
              onClick={() => setStatusFilter(s.value)}
            >
              {s.label}
              <span className="ml-1 rounded-full bg-background/60 px-1.5 text-xs tabular-nums text-muted-foreground">{counts[s.value] ?? 0}</span>
            </Button>
          ))}
        </div>
        <div className="relative w-full lg:w-72">
          <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search reference, name, destination…" className="pl-9" aria-label="Search inquiries" />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={load} /> : loading ? <TableSkeleton rows={5} cols={6} /> : visible.length === 0 ? (
          <EmptyState
            icon={FiClipboard}
            title={search || statusFilter !== 'all' ? 'No inquiries match' : 'No inquiries yet'}
            description={search || statusFilter !== 'all' ? 'Try another status or search term.' : 'Inquiries from the WhatsApp tour inquiry flow appear here.'}
            action={!search && statusFilter === 'all' ? <Button onClick={openNew}><FiPlus /> New inquiry</Button> : null}
          />
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full min-w-[760px] text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Inquiry</th>
                  <th className="px-4 py-3 font-medium">Destinations</th>
                  <th className="px-4 py-3 font-medium">When</th>
                  <th className="px-4 py-3 text-right font-medium">Travellers</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {visible.map((inq) => (
                  <tr key={inq.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <button type="button" className="text-left font-medium hover:underline" onClick={() => openEdit(inq)}>
                        {inq.lead_traveler_name || inq.customer?.full_name || 'Unnamed'}
                      </button>
                      <span className="block text-xs text-muted-foreground">
                        {inq.inquiry_reference || '—'} · {formatDate(inq.created_at)}
                      </span>
                    </td>
                    <td className="px-4 py-3">{inq.destinations || '—'}</td>
                    <td className="px-4 py-3 text-muted-foreground">{inq.preferred_dates || '—'}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{inq.number_of_travelers ?? '—'}</td>
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button type="button" className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-label="Change status">
                            <StatusBadge status={inq.status} />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          {STATUSES.map((s) => (
                            <DropdownMenuItem key={s.value} onClick={() => changeStatus(inq, s.value)} disabled={s.value === inq.status}>
                              <StatusBadge status={s.value} />
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" aria-label="Inquiry actions"><FiMoreHorizontal /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(inq)}><FiEdit2 className="size-4" /> Edit</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => remove(inq)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialog open={dialog.open} onOpenChange={(open) => setDialog((d) => ({ ...d, open }))}>
        <DialogContent className="sm:max-w-2xl">
          <form onSubmit={save} className="space-y-4">
            <DialogHeader>
              <DialogTitle>{dialog.id ? 'Edit inquiry' : 'New inquiry'}</DialogTitle>
              <DialogDescription>Capture what the customer is looking for so an agent can prepare a proposal.</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label htmlFor="inq-customer" className="mb-1.5">Customer</Label>
                <CustomerPicker
                  id="inq-customer"
                  value={form.customer_id}
                  initialLabel={form.customer_label}
                  onChange={(id, label) => setForm((f) => ({
                    ...f, customer_id: id, customer_label: label || '',
                    lead_traveler_name: f.lead_traveler_name || label || '',
                  }))}
                />
              </div>
              <div>
                <Label htmlFor="inq-lead" className="mb-1.5">Lead traveller</Label>
                <Input id="inq-lead" value={form.lead_traveler_name} onChange={set('lead_traveler_name')} />
              </div>
              <div>
                <Label htmlFor="inq-status" className="mb-1.5">Status</Label>
                <select id="inq-status" className={selectClass} value={form.status} onChange={set('status')}>
                  {STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="inq-dest" className="mb-1.5">Destinations</Label>
                <Input id="inq-dest" value={form.destinations} onChange={set('destinations')} placeholder="e.g. Victoria Falls, Chobe" required />
              </div>
              <div>
                <Label htmlFor="inq-dates" className="mb-1.5">Preferred dates</Label>
                <Input id="inq-dates" value={form.preferred_dates} onChange={set('preferred_dates')} placeholder="e.g. mid-December" />
              </div>
              <div>
                <Label htmlFor="inq-pax" className="mb-1.5">Number of travellers</Label>
                <Input id="inq-pax" type="number" min="1" value={form.number_of_travelers} onChange={set('number_of_travelers')} />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="inq-notes" className="mb-1.5">Notes</Label>
                <Textarea id="inq-notes" rows={3} value={form.notes} onChange={set('notes')} placeholder="Budget, interests, accessibility needs…" />
              </div>
            </div>
            {formError && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{formError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialog({ open: false, id: null })}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving ? 'Saving…' : dialog.id ? 'Save changes' : 'Create inquiry'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
