import React, { useEffect, useMemo, useState } from "react";
import { FiCheckCircle, FiEdit2, FiLoader, FiPlus, FiRefreshCw, FiUserCheck, FiUserX } from "react-icons/fi";
import { Button } from "@/components/ui/button";
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { adminApi } from '@/services/admin';
import { toast } from 'sonner';

const emptyForm = {
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  is_staff: true,
  is_superuser: false,
  is_active: true,
  groups: [],
};

export default function UsersCrudPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const roleLookup = useMemo(
    () => Object.fromEntries(roles.map((role) => [role.id, role.name])),
    [roles]
  );

  async function loadData() {
    setIsLoading(true);
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        adminApi.listUsers(),
        adminApi.listRoles(),
      ]);
      setUsers(usersResponse.results);
      setRoles(rolesResponse.results);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function openCreate() {
    setEditingUser(null);
    setForm(emptyForm);
    setDialogOpen(true);
  }

  function openEdit(user) {
    setEditingUser(user);
    setForm({
      username: user.username || '',
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      password: '',
      is_staff: !!user.is_staff,
      is_superuser: !!user.is_superuser,
      is_active: !!user.is_active,
      groups: user.groups || [],
    });
    setDialogOpen(true);
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function toggleGroup(groupId, checked) {
    setForm((current) => ({
      ...current,
      groups: checked
        ? [...current.groups, groupId]
        : current.groups.filter((existingId) => existingId !== groupId),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        is_staff: form.is_staff,
        is_superuser: form.is_superuser,
        is_active: form.is_active,
        groups: form.groups,
      };

      if (form.password.trim()) {
        payload.password = form.password.trim();
      }

      if (editingUser) {
        await adminApi.updateUser(editingUser.id, payload);
        toast.success('User updated.');
      } else {
        if (!payload.password) {
          toast.error('Password is required for a new user.');
          return;
        }
        await adminApi.createUser(payload);
        toast.success('User created.');
      }

      setDialogOpen(false);
      setForm(emptyForm);
      setEditingUser(null);
      await loadData();
    } finally {
      setIsSaving(false);
    }
  }

  async function handleStatusToggle(user) {
    if (user.is_active) {
      await adminApi.deactivateUser(user.id);
      toast.success(`Deactivated ${user.username}.`);
    } else {
      await adminApi.activateUser(user.id);
      toast.success(`Reactivated ${user.username}.`);
    }
    await loadData();
  }

  return (
    <section className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Users CRUD</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">Create, update, and disable frontend admin users.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2" onClick={loadData}><FiRefreshCw className="h-4 w-4" />Refresh</Button>
          <Button className="gap-2 bg-cyan-600 text-white hover:bg-cyan-700" onClick={openCreate}><FiPlus className="h-4 w-4" />New user</Button>
        </div>
      </header>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <Table>
          <TableHeader className="bg-slate-50 dark:bg-slate-800/70">
            <TableRow>
              {["Username", "Name", "Email", "Groups", "Status", "Actions"].map((col) => (
                <TableHead key={col} className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">{col}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-300">
                  <FiLoader className="mx-auto mb-2 h-5 w-5 animate-spin" />
                  Loading users...
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-300">
                  No users returned by the admin API.
                </TableCell>
              </TableRow>
            ) : users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-200">{user.username}</TableCell>
                <TableCell className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">{`${user.first_name || ''} ${user.last_name || ''}`.trim() || 'No name'}</TableCell>
                <TableCell className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">{user.email || 'No email'}</TableCell>
                <TableCell className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">
                  <div className="flex flex-wrap gap-2">
                    {(user.group_names || []).length > 0 ? user.group_names.map((groupName) => (
                      <Badge key={groupName} variant="outline">{groupName}</Badge>
                    )) : <Badge variant="secondary">{user.is_superuser ? 'superuser' : user.is_staff ? 'staff' : 'user'}</Badge>}
                  </div>
                </TableCell>
                <TableCell className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">
                  <Badge variant={user.is_active ? 'default' : 'secondary'}>{user.is_active ? 'Active' : 'Inactive'}</Badge>
                </TableCell>
                <TableCell className="px-4 py-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Button size="sm" variant="outline" className="gap-1" onClick={() => openEdit(user)}>
                      <FiEdit2 className="h-3.5 w-3.5" />Edit
                    </Button>
                    <Button
                      size="sm"
                      variant={user.is_active ? 'destructive' : 'outline'}
                      className="gap-1"
                      onClick={() => handleStatusToggle(user)}
                    >
                      {user.is_active ? <FiUserX className="h-3.5 w-3.5" /> : <FiUserCheck className="h-3.5 w-3.5" />}
                      {user.is_active ? 'Disable' : 'Activate'}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingUser ? 'Edit User' : 'Create User'}</DialogTitle>
            <DialogDescription>Manage user identity, staff access, and group assignments.</DialogDescription>
          </DialogHeader>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input id="username" value={form.username} onChange={(event) => updateField('username', event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={form.email} onChange={(event) => updateField('email', event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="first_name">First name</Label>
                <Input id="first_name" value={form.first_name} onChange={(event) => updateField('first_name', event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last name</Label>
                <Input id="last_name" value={form.last_name} onChange={(event) => updateField('last_name', event.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password {editingUser ? '(leave blank to keep current password)' : ''}</Label>
              <Input id="password" type="password" value={form.password} onChange={(event) => updateField('password', event.target.value)} />
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {[
                ['is_staff', 'Staff access'],
                ['is_superuser', 'Superuser'],
                ['is_active', 'Active'],
              ].map(([field, label]) => (
                <label key={field} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-700">
                  <Checkbox checked={form[field]} onCheckedChange={(checked) => updateField(field, Boolean(checked))} />
                  <span>{label}</span>
                </label>
              ))}
            </div>

            <div className="space-y-3">
              <Label>Group assignments</Label>
              <div className="grid grid-cols-1 gap-2 rounded-xl border border-slate-200 p-3 md:grid-cols-2 dark:border-slate-700">
                {roles.map((role) => (
                  <label key={role.id} className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                    <Checkbox
                      checked={form.groups.includes(role.id)}
                      onCheckedChange={(checked) => toggleGroup(role.id, Boolean(checked))}
                    />
                    <span>{role.name}</span>
                  </label>
                ))}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-cyan-600 text-white hover:bg-cyan-700" disabled={isSaving}>
                {isSaving ? <FiLoader className="h-4 w-4 animate-spin" /> : <FiCheckCircle className="h-4 w-4" />}
                {editingUser ? 'Save changes' : 'Create user'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </section>
  );
}
