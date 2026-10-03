import React, { useEffect, useRef, useState } from 'react';
import { useDebounce } from 'use-debounce';
import { FiSearch, FiX } from 'react-icons/fi';
import { contactsApi } from '@/lib/api';
import InitialsAvatar from './InitialsAvatar';

/**
 * Search WhatsApp contacts by name or number and pick one. The value is the
 * contact id, which is also the CustomerProfile primary key used by bookings
 * and inquiries.
 */
export default function CustomerPicker({ id, value, initialLabel = '', onChange, placeholder = 'Search name or phone…' }) {
  const [query, setQuery] = useState('');
  const [debounced] = useDebounce(query, 250);
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState(initialLabel);
  const box = useRef(null);

  useEffect(() => setLabel(initialLabel), [initialLabel]);

  useEffect(() => {
    if (!open) return undefined;
    let cancelled = false;
    contactsApi.list({ search: debounced, page_size: 8 })
      .then((res) => { if (!cancelled) setResults((res.data.results || res.data || []).slice(0, 8)); })
      .catch(() => { if (!cancelled) setResults([]); });
    return () => { cancelled = true; };
  }, [debounced, open]);

  useEffect(() => {
    const close = (e) => { if (box.current && !box.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  if (value && label) {
    return (
      <div className="flex h-9 items-center justify-between gap-2 rounded-md border bg-background px-3 text-sm">
        <span className="flex min-w-0 items-center gap-2">
          <InitialsAvatar name={label} size="sm" className="!size-6 !text-[10px]" />
          <span className="truncate">{label}</span>
        </span>
        <button type="button" className="text-muted-foreground hover:text-foreground" aria-label="Clear customer"
          onClick={() => { onChange(null); setLabel(''); }}>
          <FiX className="size-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={box}>
      <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
      <input
        id={id}
        className="h-9 w-full rounded-md border border-input bg-transparent pl-9 pr-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
        value={query}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        autoComplete="off"
        role="combobox"
        aria-expanded={open}
      />
      {open && (
        <ul className="absolute z-50 mt-1 max-h-64 w-full overflow-auto rounded-md border bg-popover p-1 shadow-lg" role="listbox">
          {results.length === 0 && <li role="presentation" className="px-3 py-2 text-sm text-muted-foreground">No matching contacts</li>}
          {results.map((c) => (
            <li key={c.id} role="presentation">
              <button
                type="button"
                role="option"
                aria-selected={false}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-accent focus-visible:bg-accent focus-visible:outline-none"
                onClick={() => {
                  const name = c.name || c.whatsapp_id;
                  setLabel(name);
                  setOpen(false);
                  setQuery('');
                  onChange(c.id, name);
                }}
              >
                <InitialsAvatar name={c.name || c.whatsapp_id} size="sm" className="!size-6 !text-[10px]" />
                <span className="min-w-0 flex-1 truncate">{c.name || 'Unnamed'}</span>
                <span className="text-xs text-muted-foreground">{c.whatsapp_id}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
