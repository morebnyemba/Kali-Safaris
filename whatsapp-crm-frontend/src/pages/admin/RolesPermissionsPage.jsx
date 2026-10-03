// src/pages/admin/RolesPermissionsPage.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { FiEdit2, FiLock, FiPlus, FiSearch, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { adminApi } from '@/services/admin';
import { apiErrorMessage } from '@/lib/format';

// Only permissions for apps the dashboard actually uses are worth showing;
// the rest (sessions, celery, token blacklist…) are framework internals.
const APPS = {
  customer_data: 'Bookings, customers & inquiries',
  conversations: 'Inbox & contacts',
  flows: 'Flows',
  media_manager: 'Media library',
  products_and_services: 'Tours & products',
  meta_integration: 'WhatsApp settings',
};
const VERBS = { view: 'View', add: 'Add', change: 'Edit', delete: 'Delete' };

function splitPermission(p) {
  const [app] = p.label.split('.');
  const verb = p.codename.split('_')[0];
  const model = p.name.replace(/^Can (view|add|change|delete) /i, '');
  return { app, verb: VERBS[verb] ? verb : null, model };
}

function RoleDialog({ open, onOpenChange, role, permissions, onSaved }) {
  const [name, setName] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [filter, setFilter] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName(role?.name || '');
    setSelected(new Set((role?.permissions || []).map((p) => p.id)));
    setFilter('');
    setError('');
  }, [open, role]);

  // { app: { model: { verb: permission } } }
  const matrix = useMemo(() => {
    const out = {};
    permissions.forEach((p) => {
      const { app, verb, model } = splitPermission(p);
      if (!APPS[app] || !verb) return;
      out[app] ??= {};
      out[app][model] ??= {};
      out[app][model][verb] = p;
    });
    return out;
  }, [permissions]);

  const toggle = (ids, on) => setSelected((prev) => {
    const next = new Set(prev);
    ids.forEach((id) => (on ? next.add(id) : next.delete(id)));
    return next;
  });

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { name: name.trim(), permission_ids: [...selected] };
      if (role) await adminApi.updateRole(role.id, payload);
      else await adminApi.createRole(payload);
      toast.success(role ? 'Role saved' : 'Role created');
      onOpenChange(false);
      onSaved();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not save this role'));
    } finally {
      setSaving(false);
    }
  };

  const q = filter.trim().toLowerCase();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col gap-0 p-0 sm:max-w-3xl">
        <form onSubmit={submit} className="flex min-h-0 flex-1 flex-col">
          <DialogHeader className="border-b p-5">
            <DialogTitle>{role ? `Edit ${role.name}` : 'New role'}</DialogTitle>
            <DialogDescription>Choose what people with this role can do. {selected.size} permissions selected.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 border-b p-5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <Label htmlFor="r-name" className="mb-1.5">Role name <span className="text-destructive">*</span></Label>
                <Input id="r-name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. reservations" />
              </div>
              <div>
                <Label htmlFor="r-filter" className="mb-1.5">Filter</Label>
                <Input id="r-filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="booking, payment…" />
              </div>
            </div>
            {name.trim().toLowerCase() === 'admin' && (
              <p className="text-xs text-warning">Members of a role named “admin” get full Administrator access to the dashboard.</p>
            )}
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            {Object.entries(APPS).filter(([app]) => matrix[app]).map(([app, appLabel]) => {
              const models = Object.entries(matrix[app]).filter(([model]) => !q || model.toLowerCase().includes(q) || appLabel.toLowerCase().includes(q));
              if (!models.length) return null;
              const ids = models.flatMap(([, verbs]) => Object.values(verbs).map((p) => p.id));
              const all = ids.every((id) => selected.has(id));
              return (
                <section key={app} className="mb-5">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-sm font-semibold">{appLabel}</h3>
                    <Button type="button" size="sm" variant="ghost" onClick={() => toggle(ids, !all)}>{all ? 'Clear all' : 'Select all'}</Button>
                  </div>
                  <div className="relative overflow-x-auto rounded-lg border">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50 text-xs text-muted-foreground">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">Item</th>
                          {Object.values(VERBS).map((v) => <th key={v} className="w-16 px-2 py-2 text-center font-medium">{v}</th>)}
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {models.map(([model, verbs]) => (
                          <tr key={model}>
                            <td className="px-3 py-1.5 capitalize">{model}</td>
                            {Object.keys(VERBS).map((verb) => (
                              <td key={verb} className="px-2 py-1.5 text-center">
                                {verbs[verb] && (
                                  <Checkbox aria-label={verbs[verb].name} checked={selected.has(verbs[verb].id)} onCheckedChange={(on) => toggle([verbs[verb].id], !!on)} />
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              );
            })}
          </div>
          <DialogFooter className="items-center border-t p-4">
            {error && <p role="alert" className="mr-auto text-sm text-destructive">{error}</p>}
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? 'Saving…' : role ? 'Save role' : 'Create role'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function RolesPermissionsPage() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [dialog, setDialog] = useState({ open: false, role: null });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [r, p] = await Promise.all([adminApi.listRoles({ page_size: 100 }), adminApi.listPermissions()]);
      setRoles(r.results);
      setPermissions(p);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (role) => {
    if (!window.confirm(`Delete the “${role.name}” role? Its members lose these permissions immediately.`)) return;
    try {
      await adminApi.deleteRole(role.id);
      toast.success('Role deleted');
      load();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const visible = roles.filter((r) => !query.trim() || r.name.toLowerCase().includes(query.trim().toLowerCase()));

  return (
    <>
      <PageHeader
        title="Roles"
        description="Bundles of permissions you assign to users. Changes apply the next time a user signs in."
        actions={<Button onClick={() => setDialog({ open: true, role: null })}><FiPlus /> New role</Button>}
      />
      <div className="relative mb-4 sm:w-72">
        <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search roles" className="pl-9" aria-label="Search roles" />
      </div>
      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={load} /> : loading ? <TableSkeleton rows={3} cols={3} /> : visible.length === 0 ? (
          <EmptyState icon={FiLock} title={roles.length ? 'No roles match' : 'No roles yet'} description={roles.length ? undefined : 'Create a role, then assign it to users.'} />
        ) : (
          <ul className="divide-y">
            {visible.map((role) => {
              const apps = [...new Set((role.permissions || []).map((p) => p.label.split('.')[0]).filter((a) => APPS[a]))];
              return (
                <li key={role.id} className="flex items-center gap-3 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{role.name}</p>
                    <p className="truncate text-sm text-muted-foreground">
                      {role.permissions?.length ? `${role.permissions.length} permissions · ${apps.map((a) => APPS[a]).join(', ') || 'system only'}` : 'No permissions'}
                    </p>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => setDialog({ open: true, role })}><FiEdit2 /> Edit</Button>
                  <Button size="icon" variant="ghost" className="text-destructive" onClick={() => remove(role)} aria-label={`Delete ${role.name}`}><FiTrash2 /></Button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
      <RoleDialog open={dialog.open} role={dialog.role} permissions={permissions} onSaved={load} onOpenChange={(open) => setDialog((d) => ({ ...d, open }))} />
    </>
  );
}
