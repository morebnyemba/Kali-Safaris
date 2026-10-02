// src/pages/ContactsPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import {
  FiAlertCircle, FiArrowLeft, FiCalendar, FiClipboard, FiEdit2, FiMail, FiMapPin, FiMessageSquare,
  FiPhone, FiSearch, FiSlash, FiUsers,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import InitialsAvatar from '@/components/app/InitialsAvatar';
import StatusBadge from '@/components/app/StatusBadge';
import { EmptyState, LoadingState } from '@/components/app/States';
import { contactsApi, inquiriesApi, profilesApi } from '@/lib/api';
import { ordersApi } from '@/services/orders';
import { apiErrorMessage, formatDate, formatMoney, formatRelative } from '@/lib/format';

const LEAD_STATUSES = [
  ['new', 'New'], ['contacted', 'Contacted'], ['qualified', 'Qualified'], ['proposal_sent', 'Proposal sent'],
  ['negotiation', 'Negotiation'], ['won', 'Won'], ['lost', 'Lost'], ['on_hold', 'On hold'],
];
const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'attention', label: 'Needs a human' },
  { key: 'blocked', label: 'Blocked' },
];
const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

function Field({ label, children }) {
  return (
    <div className="grid grid-cols-3 gap-3 py-2.5 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="col-span-2 break-words">{children || <span className="text-muted-foreground">—</span>}</dd>
    </div>
  );
}

function EditContactDialog({ open, onOpenChange, contact, profile, onSaved }) {
  const [form, setForm] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !contact) return;
    setError('');
    setForm({
      name: contact.name || '',
      is_blocked: Boolean(contact.is_blocked),
      needs_human_intervention: Boolean(contact.needs_human_intervention),
      first_name: profile?.first_name || '', last_name: profile?.last_name || '', email: profile?.email || '',
      company: profile?.company || '', role: profile?.role || '',
      address_line_1: profile?.address_line_1 || '', address_line_2: profile?.address_line_2 || '',
      city: profile?.city || '', state_province: profile?.state_province || '', postal_code: profile?.postal_code || '',
      country: profile?.country || '', lead_status: profile?.lead_status || 'new',
      acquisition_source: profile?.acquisition_source || '', potential_value: profile?.potential_value ?? '',
      tags: (profile?.tags || []).join(', '), notes: profile?.notes || '',
    });
  }, [open, contact, profile]);

  if (!form) return null;
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const input = (field, label, props = {}) => (
    <div>
      <Label htmlFor={`c-${field}`} className="mb-1.5">{label}</Label>
      <Input id={`c-${field}`} value={form[field]} onChange={set(field)} {...props} />
    </div>
  );

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await contactsApi.patch(contact.id, {
        name: form.name, is_blocked: form.is_blocked, needs_human_intervention: form.needs_human_intervention,
      });
      await profilesApi.patch(contact.id, {
        first_name: form.first_name, last_name: form.last_name, email: form.email || null,
        company: form.company, role: form.role,
        address_line_1: form.address_line_1, address_line_2: form.address_line_2, city: form.city,
        state_province: form.state_province, postal_code: form.postal_code, country: form.country,
        lead_status: form.lead_status, acquisition_source: form.acquisition_source,
        potential_value: form.potential_value === '' ? null : form.potential_value,
        tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
        notes: form.notes,
      });
      toast.success('Contact saved');
      onOpenChange(false);
      onSaved();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <form onSubmit={save} className="space-y-5">
          <DialogHeader>
            <DialogTitle>Edit {contact.name || contact.whatsapp_id}</DialogTitle>
            <DialogDescription>WhatsApp {contact.whatsapp_id}</DialogDescription>
          </DialogHeader>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Contact</h3>
            {input('name', 'Display name')}
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-8">
              <label className="flex items-center gap-2 text-sm">
                <Switch checked={form.needs_human_intervention} onCheckedChange={(v) => setForm((f) => ({ ...f, needs_human_intervention: v }))} />
                Bot paused (needs a human)
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Switch checked={form.is_blocked} onCheckedChange={(v) => setForm((f) => ({ ...f, is_blocked: v }))} />
                Blocked
              </label>
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Profile</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {input('first_name', 'First name')}
              {input('last_name', 'Last name')}
              {input('email', 'Email', { type: 'email' })}
              {input('country', 'Country')}
              {input('company', 'Company')}
              {input('role', 'Role / job title')}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Address</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {input('address_line_1', 'Address line 1')}
              {input('address_line_2', 'Address line 2')}
              {input('city', 'City')}
              {input('state_province', 'State / province')}
              {input('postal_code', 'Postal code')}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Sales</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <Label htmlFor="c-lead_status" className="mb-1.5">Lead status</Label>
                <select id="c-lead_status" className={selectClass} value={form.lead_status} onChange={set('lead_status')}>
                  {LEAD_STATUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              {input('potential_value', 'Potential value (USD)', { type: 'number', min: 0, step: '0.01' })}
              {input('acquisition_source', 'Source', { placeholder: 'e.g. WhatsApp, referral, website' })}
              {input('tags', 'Tags', { placeholder: 'comma, separated' })}
            </div>
            <div>
              <Label htmlFor="c-notes" className="mb-1.5">Notes</Label>
              <Textarea id="c-notes" rows={3} value={form.notes} onChange={set('notes')} />
            </div>
          </section>

          {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save contact'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ContactDetail({ contactId, onBack, onChanged }) {
  const navigate = useNavigate();
  const [contact, setContact] = useState(null);
  const [profile, setProfile] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [inquiries, setInquiries] = useState([]);
  const [tab, setTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [c, p, b, i] = await Promise.allSettled([
        contactsApi.retrieve(contactId),
        profilesApi.retrieve(contactId),
        ordersApi.list({ customer: contactId, page_size: 50 }),
        inquiriesApi.list({ customer: contactId, page_size: 50 }),
      ]);
      if (c.status === 'fulfilled') setContact(c.value.data);
      setProfile(p.status === 'fulfilled' ? p.value.data : null);
      setBookings(b.status === 'fulfilled' ? (b.value.data.results || b.value.data) : []);
      setInquiries(i.status === 'fulfilled' ? (i.value.data.results || i.value.data) : []);
    } finally {
      setLoading(false);
    }
  }, [contactId]);

  useEffect(() => { setTab('profile'); load(); }, [load]);

  if (loading && !contact) return <LoadingState label="Loading contact…" />;
  if (!contact) return <EmptyState icon={FiUsers} title="Contact not found" />;

  const name = contact.name || contact.whatsapp_id;
  const fullName = [profile?.first_name, profile?.last_name].filter(Boolean).join(' ');
  const address = [profile?.address_line_1, profile?.address_line_2, [profile?.city, profile?.state_province].filter(Boolean).join(', '), [profile?.postal_code, profile?.country].filter(Boolean).join(' ')].filter(Boolean);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4 sm:p-6">
        <Button variant="ghost" size="sm" className="-ml-2 mb-2 md:hidden" onClick={onBack}><FiArrowLeft /> Contacts</Button>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-4">
            <InitialsAvatar name={name} size="lg" />
            <div className="min-w-0">
              <h2 className="truncate text-xl font-semibold">{name}</h2>
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
                <span className="flex items-center gap-1"><FiPhone className="size-3.5" /> {contact.whatsapp_id}</span>
                {profile?.email && <span className="flex items-center gap-1"><FiMail className="size-3.5" /> {profile.email}</span>}
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {contact.needs_human_intervention && <StatusBadge tone="warning" label="Needs a human" />}
                {contact.is_blocked && <StatusBadge tone="danger" label="Blocked" />}
                {profile?.lead_status_display && <StatusBadge tone="info" label={profile.lead_status_display} />}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate(`/conversation?contactId=${contact.id}`)}><FiMessageSquare /> Open chat</Button>
            <Button size="sm" onClick={() => setEditOpen(true)}><FiEdit2 /> Edit</Button>
          </div>
        </div>
        <div className="mt-5 flex gap-1" role="tablist">
          {[['profile', 'Profile'], ['bookings', `Bookings (${bookings.length})`], ['inquiries', `Inquiries (${inquiries.length})`]].map(([key, label]) => (
            <Button key={key} role="tab" aria-selected={tab === key} size="sm" variant={tab === key ? 'secondary' : 'ghost'} onClick={() => setTab(key)}>{label}</Button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {tab === 'profile' && (
          <dl className="divide-y">
            <Field label="Full name">{fullName}</Field>
            <Field label="Company">{[profile?.company, profile?.role].filter(Boolean).join(' · ')}</Field>
            <Field label="Address">{address.length > 0 && <span className="flex gap-1.5"><FiMapPin className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" /><span>{address.map((l) => <span key={l} className="block">{l}</span>)}</span></span>}</Field>
            <Field label="Source">{profile?.acquisition_source}</Field>
            <Field label="Potential value">{profile?.potential_value ? formatMoney(profile.potential_value) : null}</Field>
            <Field label="Tags">{profile?.tags?.length > 0 && <span className="flex flex-wrap gap-1">{profile.tags.map((t) => <StatusBadge key={t} label={t} />)}</span>}</Field>
            <Field label="Notes">{profile?.notes && <span className="whitespace-pre-wrap">{profile.notes}</span>}</Field>
            <Field label="First contact">{formatDate(contact.first_seen)}</Field>
            <Field label="Last seen">{contact.last_seen ? `${formatDate(contact.last_seen)} (${formatRelative(contact.last_seen)})` : null}</Field>
          </dl>
        )}
        {tab === 'bookings' && (bookings.length === 0 ? (
          <EmptyState icon={FiCalendar} title="No bookings yet" action={<Button asChild size="sm" variant="outline"><Link to="/bookings">Go to bookings</Link></Button>} />
        ) : (
          <ul className="divide-y rounded-lg border">
            {bookings.map((b) => (
              <li key={b.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
                <span className="min-w-0">
                  <span className="block font-medium">{b.tour_name}</span>
                  <span className="text-xs text-muted-foreground">{b.booking_reference} · {formatDate(b.start_date)} · {(b.number_of_adults || 0) + (b.number_of_children || 0)} pax</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className="tabular-nums">{formatMoney(b.total_amount)}</span>
                  <StatusBadge status={b.payment_status} />
                </span>
              </li>
            ))}
          </ul>
        ))}
        {tab === 'inquiries' && (inquiries.length === 0 ? (
          <EmptyState icon={FiClipboard} title="No inquiries yet" />
        ) : (
          <ul className="divide-y rounded-lg border">
            {inquiries.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
                <span className="min-w-0">
                  <span className="block font-medium">{i.destinations || 'Custom tour'}</span>
                  <span className="text-xs text-muted-foreground">{i.inquiry_reference} · {i.preferred_dates || 'dates open'} · {i.number_of_travelers ?? '?'} travellers</span>
                </span>
                <StatusBadge status={i.status} />
              </li>
            ))}
          </ul>
        ))}
      </div>

      <EditContactDialog open={editOpen} onOpenChange={setEditOpen} contact={contact} profile={profile}
        onSaved={() => { load(); onChanged(); }} />
    </div>
  );
}

export default function ContactsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [contacts, setContacts] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebounce(search, 300);
  const [filter, setFilter] = useState(searchParams.get('filter') === 'needs_intervention' ? 'attention' : 'all');
  const selectedId = Number(searchParams.get('contactId')) || null;

  const load = useCallback(async (pageToLoad = 1) => {
    setLoading(true);
    try {
      const res = await contactsApi.list({
        page: pageToLoad,
        search: debouncedSearch || undefined,
        needs_human_intervention: filter === 'attention' ? 'true' : undefined,
      });
      const results = res.data.results || [];
      const visible = filter === 'blocked' ? results.filter((c) => c.is_blocked) : results;
      setContacts((prev) => (pageToLoad === 1 ? visible : [...prev, ...visible]));
      setCount(res.data.count ?? results.length);
      setHasMore(Boolean(res.data.next));
      setPage(pageToLoad);
    } catch (err) {
      toast.error(apiErrorMessage(err, "Couldn't load contacts"));
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, filter]);

  useEffect(() => { load(1); }, [load]);

  const select = (id) => {
    const next = new URLSearchParams(searchParams);
    if (id) next.set('contactId', id); else next.delete('contactId');
    setSearchParams(next, { replace: !id });
  };

  return (
    <div className="-my-2 flex h-[calc(100dvh-9.5rem)] min-h-[480px] overflow-hidden rounded-xl border bg-card">
      <section className={`${selectedId ? 'hidden md:flex' : 'flex'} w-full flex-col border-r md:w-80 lg:w-96`} aria-label="Contacts">
        <div className="space-y-3 border-b p-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Contacts</h2>
            <span className="text-xs text-muted-foreground">{count} total</span>
          </div>
          <div className="relative">
            <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input type="search" placeholder="Search name or number…" className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search contacts" />
          </div>
          <div className="flex gap-1">
            {FILTERS.map((f) => (
              <Button key={f.key} size="sm" variant={filter === f.key ? 'secondary' : 'ghost'} onClick={() => setFilter(f.key)}>{f.label}</Button>
            ))}
          </div>
        </div>
        <div className="flex-1 divide-y overflow-y-auto">
          {loading && contacts.length === 0 ? <LoadingState label="Loading contacts…" /> : contacts.length === 0 ? (
            <EmptyState icon={FiUsers} title="No contacts found" description={search ? 'Try a different name or number.' : 'Customers appear here after they message you on WhatsApp.'} />
          ) : (
            <>
              {contacts.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => select(c.id)}
                  className={`flex w-full items-center gap-3 border-l-[3px] px-3 py-3 text-left transition-colors ${selectedId === c.id ? 'border-l-brand-accent bg-accent' : 'border-l-transparent hover:bg-muted/60'}`}
                >
                  <InitialsAvatar name={c.name || c.whatsapp_id} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{c.name || c.whatsapp_id}</span>
                    <span className="block truncate text-xs text-muted-foreground">{c.whatsapp_id}{c.last_seen && ` · seen ${formatRelative(c.last_seen)}`}</span>
                  </span>
                  {c.needs_human_intervention && <FiAlertCircle className="size-4 shrink-0 text-warning" aria-label="Needs a human" />}
                  {c.is_blocked && <FiSlash className="size-4 shrink-0 text-destructive" aria-label="Blocked" />}
                </button>
              ))}
              {hasMore && (
                <div className="p-3">
                  <Button variant="outline" size="sm" className="w-full" onClick={() => load(page + 1)} disabled={loading}>
                    {loading ? 'Loading…' : 'Load more'}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      <section className={`${selectedId ? 'flex' : 'hidden md:flex'} min-w-0 flex-1 flex-col`} aria-label="Contact details">
        {selectedId ? (
          <ContactDetail key={selectedId} contactId={selectedId} onBack={() => select(null)} onChanged={() => load(1)} />
        ) : (
          <EmptyState icon={FiUsers} title="Select a contact" description="See their profile, bookings and inquiries, or jump to their WhatsApp chat." className="m-auto" />
        )}
      </section>
    </div>
  );
}
