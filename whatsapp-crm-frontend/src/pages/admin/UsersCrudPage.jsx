// src/pages/admin/UsersCrudPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import { FiEdit2, FiMoreHorizontal, FiSearch, FiUserCheck, FiUserPlus, FiUsers, FiUserX } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import InitialsAvatar from '@/components/app/InitialsAvatar';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { useAuth } from '@/context/AuthContext';
import { adminApi } from '@/services/admin';
import { apiErrorMessage, formatRelative } from '@/lib/format';

const LEVELS = [
  { key: 'agent', label: 'Agent', description: 'Inbox, bookings, inquiries, contacts and flows.' },
  { key: 'manager', label: 'Manager', description: 'Everything agents can do, plus WhatsApp settings and the audit log.' },
  { key: 'admin', label: 'Administrator', description: 'Full access, including users and roles.' },
];
const LEVEL_TONE = { admin: 'bg-brand-accent/10 text-brand-accent', manager: 'bg-info/10 text-info', agent: 'bg-muted text-muted-foreground' };
const ADMIN_GROUPS = ['admin', 'administrators'];
const EMPTY = { username: '', first_name: '', last_name: '', email: '', password: '', level: 'agent', is_active: true, groups: [] };

function levelOf(user) {
  const groups = (user.group_names || []).map((g) => g.toLowerCase());
  if (user.is_superuser || groups.some((g) => ADMIN_GROUPS.includes(g))) return 'admin';
  return user.is_staff ? 'manager' : 'agent';
}

function UserDialog({ open, onOpenChange, user, roles, me, onSaved }) {
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const isSelf = user && user.id === me?.user_id;
  const canMakeSuperuser = !!me?.is_superuser;

  useEffect(() => {
    if (!open) return;
    setError('');
    setForm(user ? {
      username: user.username, first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '',
      password: '', level: user.is_superuser ? 'admin' : user.is_staff ? 'manager' : 'agent', is_active: user.is_active, groups: user.groups || [],
    } : EMPTY);
  }, [open, user]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e?.target ? e.target.value : e }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    const payload = {
      username: form.username.trim(), first_name: form.first_name.trim(), last_name: form.last_name.trim(), email: form.email.trim(),
      is_staff: form.level !== 'agent', groups: form.groups,
    };
    if (canMakeSuperuser) payload.is_superuser = form.level === 'admin';
    if (!isSelf) payload.is_active = form.is_active;
    if (form.password) payload.password = form.password;
    try {
      if (user) await adminApi.updateUser(user.id, payload);
      else await adminApi.createUser(payload);
      toast.success(user ? 'User updated' : 'User created');
      onOpenChange(false);
      onSaved();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not save this user'));
    } finally {
      setSaving(false);
    }
  };

  const toggleGroup = (id, on) => setForm((f) => ({ ...f, groups: on ? [...f.groups, id] : f.groups.filter((g) => g !== id) }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <form onSubmit={submit} className="space-y-5">
          <DialogHeader>
            <DialogTitle>{user ? `Edit ${user.username}` : 'New user'}</DialogTitle>
            <DialogDescription>People who sign in to this dashboard.</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="u-first" className="mb-1.5">First name</Label>
              <Input id="u-first" value={form.first_name} onChange={set('first_name')} />
            </div>
            <div>
              <Label htmlFor="u-last" className="mb-1.5">Last name</Label>
              <Input id="u-last" value={form.last_name} onChange={set('last_name')} />
            </div>
            <div>
              <Label htmlFor="u-username" className="mb-1.5">Username <span className="text-destructive">*</span></Label>
              <Input id="u-username" autoComplete="off" value={form.username} onChange={set('username')} required />
            </div>
            <div>
              <Label htmlFor="u-email" className="mb-1.5">Email</Label>
              <Input id="u-email" type="email" value={form.email} onChange={set('email')} />
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="u-password" className="mb-1.5">{user ? 'New password' : 'Password'} {!user && <span className="text-destructive">*</span>}</Label>
              <Input id="u-password" type="password" autoComplete="new-password" value={form.password} onChange={set('password')} required={!user}
                placeholder={user ? 'Leave blank to keep the current password' : ''} />
              <p className="mt-1 text-xs text-muted-foreground">At least 8 characters, not all numbers, and not a common password.</p>
            </div>
          </div>

          <fieldset>
            <legend className="mb-2 text-sm font-medium">Access level</legend>
            <div className="space-y-2">
              {LEVELS.map((l) => {
                const disabled = l.key === 'admin' && !canMakeSuperuser;
                return (
                  <label key={l.key} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${form.level === l.key ? 'border-primary bg-primary/5' : ''} ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}>
                    <input type="radio" name="level" value={l.key} checked={form.level === l.key} disabled={disabled} onChange={() => set('level')(l.key)} className="mt-1 accent-[var(--primary)]" />
                    <span>
                      <span className="block text-sm font-medium">{l.label}</span>
                      <span className="block text-xs text-muted-foreground">{disabled ? 'Only a superuser can grant this.' : l.description}</span>
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          {roles.length > 0 && (
            <fieldset>
              <legend className="mb-2 text-sm font-medium">Roles</legend>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {roles.map((r) => (
                  <label key={r.id} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={form.groups.includes(r.id)} onCheckedChange={(on) => toggleGroup(r.id, !!on)} />
                    {r.name}
                  </label>
                ))}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Members of the “admin” role also get Administrator access.</p>
            </fieldset>
          )}

          {user && !isSelf && (
            <div className="flex items-center gap-2">
              <Switch id="u-active" checked={form.is_active} onCheckedChange={set('is_active')} />
              <Label htmlFor="u-active">Can sign in</Label>
            </div>
          )}

          {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Saving…' : user ? 'Save changes' : 'Create user'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function UsersCrudPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [count, setCount] = useState(0);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [debounced] = useDebounce(query, 300);
  const [dialog, setDialog] = useState({ open: false, user: null });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [u, r] = await Promise.all([
        adminApi.listUsers({ search: debounced || undefined, page_size: 100 }),
        adminApi.listRoles({ page_size: 100 }),
      ]);
      setUsers(u.results);
      setCount(u.count);
      setRoles(r.results);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [debounced]);

  useEffect(() => { load(); }, [load]);

  const toggleActive = async (u) => {
    try {
      if (u.is_active) await adminApi.deactivateUser(u.id);
      else await adminApi.activateUser(u.id);
      toast.success(`${u.username} ${u.is_active ? 'can no longer sign in' : 'can sign in again'}`);
      load();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <>
      <PageHeader
        title="Users"
        description={loading ? 'People who can sign in to this dashboard.' : `${count} ${count === 1 ? 'person' : 'people'} can sign in to this dashboard.`}
        actions={<Button onClick={() => setDialog({ open: true, user: null })}><FiUserPlus /> New user</Button>}
      />

      <div className="relative mb-4 sm:w-72">
        <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, username or email" className="pl-9" aria-label="Search users" />
      </div>

      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={load} /> : loading && !users.length ? <TableSkeleton rows={4} cols={4} /> : users.length === 0 ? (
          <EmptyState icon={FiUsers} title={query ? 'No users match' : 'No users yet'} />
        ) : (
          <ul className="divide-y">
            {users.map((u) => {
              const level = levelOf(u);
              const name = `${u.first_name || ''} ${u.last_name || ''}`.trim();
              const isSelf = u.id === me?.user_id;
              return (
                <li key={u.id} className={`flex items-center gap-3 px-4 py-3 ${u.is_active ? '' : 'opacity-60'}`}>
                  <InitialsAvatar name={name || u.username} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">
                      {name || u.username}
                      {isSelf && <span className="ml-2 text-xs font-normal text-muted-foreground">(you)</span>}
                    </p>
                    <p className="truncate text-sm text-muted-foreground">@{u.username}{u.email ? ` · ${u.email}` : ''}</p>
                  </div>
                  <div className="hidden flex-col items-end gap-1 sm:flex">
                    <div className="flex flex-wrap justify-end gap-1">
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${LEVEL_TONE[level]}`}>{LEVELS.find((l) => l.key === level).label}</span>
                      {(u.group_names || []).filter((g) => !ADMIN_GROUPS.includes(g.toLowerCase())).map((g) => (
                        <span key={g} className="rounded-full border px-2 py-0.5 text-[11px]">{g}</span>
                      ))}
                      {!u.is_active && <span className="rounded-full bg-destructive/10 px-2 py-0.5 text-[11px] font-medium text-destructive">Disabled</span>}
                    </div>
                    {u.last_login && <span className="text-xs text-muted-foreground">Last signed in {formatRelative(u.last_login)}</span>}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label={`Actions for ${u.username}`}><FiMoreHorizontal /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setDialog({ open: true, user: u })}><FiEdit2 className="size-4" /> Edit</DropdownMenuItem>
                      {!isSelf && (
                        <DropdownMenuItem onClick={() => toggleActive(u)} className={u.is_active ? 'text-destructive focus:text-destructive' : ''}>
                          {u.is_active ? <><FiUserX className="size-4" /> Disable sign-in</> : <><FiUserCheck className="size-4" /> Enable sign-in</>}
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <UserDialog open={dialog.open} user={dialog.user} roles={roles} me={me} onSaved={load} onOpenChange={(open) => setDialog((d) => ({ ...d, open }))} />
    </>
  );
}
