import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { FileText, Loader2, Pencil, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { travelerErrorMessage, travelersApi } from '@/services/travelers';

// Mirrors customer_data/traveler_validation.py (the server is authoritative).
const ID_REQUIRED_FROM_AGE = 12;

const EMPTY_DRAFT = {
  name: '',
  age: '',
  nationality: '',
  gender: '',
  id_number: '',
  traveler_type: 'adult',
  medical_dietary_requirements: '',
  id_document: null,
  remove_id_document: false,
};

const selectClass =
  'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

const validateDraft = (draft) => {
  const age = Number(draft.age);
  if (draft.name.trim().length < 2) return 'Full name is required.';
  if (draft.age === '' || !Number.isInteger(age) || age < 0 || age > 120) {
    return 'Enter a valid age (0 for infants under one).';
  }
  if (!draft.nationality.trim()) return 'Nationality is required.';
  if (!draft.gender) return 'Select a gender.';
  if (age >= ID_REQUIRED_FROM_AGE && !draft.id_number.trim()) {
    return `ID/passport number is required from age ${ID_REQUIRED_FROM_AGE}.`;
  }
  return '';
};

/**
 * Add / edit / remove the passengers on a booking. A booking only confirms
 * (Paid / Deposit Paid) once every booked passenger here is complete; a paid
 * booking waiting on details confirms itself as soon as the list is complete.
 */
export default function PassengerEditor({ booking, onChanged }) {
  const [travelers, setTravelers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | 'new' | traveler id
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [typeTouched, setTypeTouched] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const booked = (Number(booking.number_of_adults) || 0) + (Number(booking.number_of_children) || 0);
  const problems = booking.traveler_details_problems || [];
  const complete = problems.length === 0;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await travelersApi.list(booking.id);
      setTravelers(res.data.results || res.data);
    } catch {
      toast.error('Could not load passengers.');
    } finally {
      setLoading(false);
    }
  }, [booking.id]);

  useEffect(() => {
    load();
  }, [load]);

  const startAdd = () => {
    setDraft(EMPTY_DRAFT);
    setTypeTouched(false);
    setError('');
    setEditing('new');
  };

  const startEdit = (traveler) => {
    setDraft({
      ...EMPTY_DRAFT,
      name: traveler.name || '',
      age: traveler.age ?? '',
      nationality: traveler.nationality || '',
      gender: traveler.gender || '',
      id_number: traveler.id_number || '',
      traveler_type: traveler.traveler_type || 'adult',
      medical_dietary_requirements: traveler.medical_dietary_requirements || '',
    });
    setTypeTouched(true);
    setError('');
    setEditing(traveler.id);
  };

  const cancel = () => {
    setEditing(null);
    setError('');
  };

  const setField = (field, value) => {
    setDraft((d) => {
      const next = { ...d, [field]: value };
      // Suggest the category from age until staff pick one explicitly.
      if (field === 'age' && !typeTouched && value !== '') {
        next.traveler_type = Number(value) < ID_REQUIRED_FROM_AGE ? 'child' : 'adult';
      }
      return next;
    });
  };

  const save = async () => {
    const clientError = validateDraft(draft);
    if (clientError) {
      setError(clientError);
      return;
    }
    setSaving(true);
    setError('');
    const payload = {
      ...draft,
      age: Number(draft.age),
      id_document: draft.id_document || undefined,
      remove_id_document: draft.remove_id_document || undefined,
    };
    try {
      if (editing === 'new') {
        await travelersApi.create({ ...payload, booking: booking.id });
      } else {
        await travelersApi.update(editing, payload);
      }
      setEditing(null);
      await load();
      onChanged?.();
    } catch (err) {
      setError(travelerErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (traveler) => {
    if (!window.confirm(`Remove ${traveler.name} from this booking?`)) return;
    try {
      await travelersApi.delete(traveler.id);
      await load();
      onChanged?.();
    } catch {
      // The global API interceptor already shows the error.
    }
  };

  const viewDocument = async (traveler) => {
    try {
      await travelersApi.openIdDocument(traveler.id);
    } catch {
      toast.error('Could not open the ID document.');
    }
  };

  const idRequired = draft.age === '' || Number(draft.age) >= ID_REQUIRED_FROM_AGE;
  const canAdd = travelers.length < booked;

  return (
    <section className="space-y-3 border-t pt-4" aria-labelledby="passengers-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 id="passengers-heading" className="text-base font-semibold">Passengers</h3>
          <p className={`text-sm ${complete ? 'text-muted-foreground' : 'text-amber-700 dark:text-amber-300'}`}>
            {travelers.length} of {booked} booked passenger(s) added
            {complete ? ' — complete' : ''}
          </p>
        </div>
        {editing === null && (
          <Button type="button" size="sm" onClick={startAdd} disabled={!canAdd || loading}>
            <Plus /> Add passenger
          </Button>
        )}
      </div>

      {booking.payment_status === 'awaiting_details' && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          Payment received. This booking confirms automatically once every passenger below is complete.
        </p>
      )}
      {!complete && problems.length > 0 && editing === null && (
        <ul className="list-disc pl-5 text-sm text-amber-800 dark:text-amber-200">
          {problems.map((p) => <li key={p}>{p}</li>)}
        </ul>
      )}
      {!canAdd && editing === null && travelers.length > 0 && booked > 0 && travelers.length >= booked && !complete && (
        <p className="text-sm text-muted-foreground">
          All {booked} passenger slots are used — edit a passenger to fix their details.
        </p>
      )}

      {loading ? (
        <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading passengers…</p>
      ) : (
        <ul className="divide-y rounded-md border">
          {travelers.length === 0 && (
            <li className="px-3 py-4 text-sm text-muted-foreground">No passengers yet.</li>
          )}
          {travelers.map((t) => (
            <li key={t.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
              <div className="min-w-0">
                <p className="font-medium">{t.name}</p>
                <p className="text-xs text-muted-foreground">
                  {t.age} · {t.gender} · {t.nationality} · {t.traveler_type === 'child' ? 'Child' : 'Adult'}
                  {' · '}
                  {t.id_number || (t.age < ID_REQUIRED_FROM_AGE ? `Under ${ID_REQUIRED_FROM_AGE} — no ID needed` : 'No ID number')}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {t.has_id_document ? (
                  <Button type="button" size="sm" variant="ghost" onClick={() => viewDocument(t)} aria-label={`View ID copy for ${t.name}`}>
                    <FileText /> ID copy
                  </Button>
                ) : (
                  <span className="px-2 text-xs text-muted-foreground">No ID copy</span>
                )}
                <Button type="button" size="sm" variant="ghost" onClick={() => startEdit(t)} disabled={editing !== null} aria-label={`Edit ${t.name}`}>
                  <Pencil />
                </Button>
                <Button type="button" size="sm" variant="ghost" onClick={() => remove(t)} disabled={editing !== null} aria-label={`Remove ${t.name}`}>
                  <Trash2 />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {editing !== null && (
        <div className="space-y-3 rounded-md border bg-muted/30 p-3">
          <p className="text-sm font-medium">{editing === 'new' ? 'New passenger' : 'Edit passenger'}</p>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="p-name">Full name</Label>
              <Input id="p-name" value={draft.name} onChange={(e) => setField('name', e.target.value)} autoFocus />
            </div>
            <div>
              <Label htmlFor="p-age">Age</Label>
              <Input id="p-age" type="number" min="0" max="120" value={draft.age} onChange={(e) => setField('age', e.target.value)} />
            </div>
            <div>
              <Label htmlFor="p-nationality">Nationality</Label>
              <Input id="p-nationality" value={draft.nationality} onChange={(e) => setField('nationality', e.target.value)} />
            </div>
            <div>
              <Label htmlFor="p-gender">Gender</Label>
              <select id="p-gender" className={selectClass} value={draft.gender} onChange={(e) => setField('gender', e.target.value)}>
                <option value="">Select…</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <Label htmlFor="p-type">Category</Label>
              <select
                id="p-type"
                className={selectClass}
                value={draft.traveler_type}
                onChange={(e) => { setTypeTouched(true); setField('traveler_type', e.target.value); }}
              >
                <option value="adult">Adult</option>
                <option value="child">Child</option>
              </select>
            </div>
            <div>
              <Label htmlFor="p-id">
                ID / Passport number{!idRequired && <span className="text-muted-foreground"> (optional under {ID_REQUIRED_FROM_AGE})</span>}
              </Label>
              <Input id="p-id" value={draft.id_number} onChange={(e) => setField('id_number', e.target.value)} />
            </div>
            <div>
              <Label htmlFor="p-doc">ID / Passport copy (JPG, PNG or PDF, max 5MB)</Label>
              <Input
                id="p-doc"
                type="file"
                accept="image/jpeg,image/png,application/pdf"
                onChange={(e) => setField('id_document', e.target.files?.[0] || null)}
              />
              {editing !== 'new' && travelers.find((t) => t.id === editing)?.has_id_document && !draft.id_document && (
                <label className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={draft.remove_id_document}
                    onChange={(e) => setField('remove_id_document', e.target.checked)}
                  />
                  Remove the current copy
                </label>
              )}
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="p-medical">Medical / dietary needs (optional)</Label>
              <Input id="p-medical" value={draft.medical_dietary_requirements} onChange={(e) => setField('medical_dietary_requirements', e.target.value)} />
            </div>
          </div>
          {error && (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={cancel} disabled={saving}>Cancel</Button>
            <Button type="button" size="sm" onClick={save} disabled={saving}>
              {saving && <Loader2 className="animate-spin" />} Save passenger
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
