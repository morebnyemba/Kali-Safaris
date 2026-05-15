import React, { useEffect, useMemo, useState } from "react";
import { FiCheckCircle, FiKey, FiLoader, FiLock, FiPlus } from "react-icons/fi";
import { Button } from "@/components/ui/button";
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { adminApi } from '@/services/admin';
import { toast } from 'sonner';

const emptyForm = {
  name: '',
  permission_ids: [],
};

export default function RolesPermissionsPage() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const groupedPermissions = useMemo(() => {
    return permissions.reduce((accumulator, permission) => {
      const appLabel = permission.label.split('.')[0];
      if (!accumulator[appLabel]) {
        accumulator[appLabel] = [];
      }
      accumulator[appLabel].push(permission);
      return accumulator;
    }, {});
  }, [permissions]);

  async function loadData() {
    setIsLoading(true);
    try {
      const [rolesResponse, permissionsResponse] = await Promise.all([
        adminApi.listRoles(),
        adminApi.listPermissions(),
      ]);
      setRoles(rolesResponse.results);
      setPermissions(permissionsResponse);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function openCreate() {
    setEditingRole(null);
    setForm(emptyForm);
    setDialogOpen(true);
  }

  function openEdit(role) {
    setEditingRole(role);
    setForm({
      name: role.name || '',
      permission_ids: (role.permissions || []).map((permission) => permission.id),
    });
    setDialogOpen(true);
  }

  function togglePermission(permissionId, checked) {
    setForm((current) => ({
      ...current,
      permission_ids: checked
        ? [...current.permission_ids, permissionId]
        : current.permission_ids.filter((existingId) => existingId !== permissionId),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        name: form.name,
        permission_ids: form.permission_ids,
      };

      if (editingRole) {
        await adminApi.updateRole(editingRole.id, payload);
        toast.success('Role updated.');
      } else {
        await adminApi.createRole(payload);
        toast.success('Role created.');
      }

      setDialogOpen(false);
      setEditingRole(null);
      setForm(emptyForm);
      await loadData();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="space-y-5">
      <header className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <FiLock className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Roles & Permissions</h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">Define RBAC matrix for all frontend admin actions.</p>
          </div>
        </div>
      </header>

      <div className="flex justify-end">
        <Button className="gap-2 bg-cyan-600 text-white hover:bg-cyan-700" onClick={openCreate}>
          <FiPlus className="h-4 w-4" />New role
        </Button>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <Table>
          <TableHeader className="bg-slate-50 dark:bg-slate-800/70">
            <TableRow>
              {["Role", "Permission Count", "Permission Preview", "Action"].map((col) => (
                <TableHead key={col} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">{col}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-300">
                  <FiLoader className="mx-auto mb-2 h-5 w-5 animate-spin" />
                  Loading roles...
                </TableCell>
              </TableRow>
            ) : roles.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-300">
                  No backend roles found.
                </TableCell>
              </TableRow>
            ) : roles.map((role) => (
              <TableRow key={role.id}>
                <TableCell className="px-4 py-3 text-sm font-medium text-slate-800 dark:text-slate-100">{role.name}</TableCell>
                <TableCell className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{(role.permissions || []).length}</TableCell>
                <TableCell className="max-w-xl px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                  {(role.permissions || []).slice(0, 4).map((permission) => permission.label).join(', ') || 'No permissions'}
                  {(role.permissions || []).length > 4 ? '...' : ''}
                </TableCell>
                <TableCell className="px-4 py-3 text-sm">
                  <Button size="sm" variant="outline" className="gap-1" onClick={() => openEdit(role)}>
                    <FiKey className="h-3.5 w-3.5" />Edit Policy
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{editingRole ? 'Edit Role' : 'Create Role'}</DialogTitle>
            <DialogDescription>Assign Django permissions that drive frontend and backend admin access.</DialogDescription>
          </DialogHeader>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="role-name">Role name</Label>
              <Input id="role-name" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
            </div>

            <div className="space-y-3">
              <Label>Permissions</Label>
              <div className="max-h-96 space-y-4 overflow-y-auto rounded-xl border border-slate-200 p-4 dark:border-slate-700">
                {Object.entries(groupedPermissions).map(([appLabel, permissionGroup]) => (
                  <div key={appLabel} className="space-y-2">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-200">{appLabel}</h3>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                      {permissionGroup.map((permission) => (
                        <label key={permission.id} className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                          <Checkbox
                            checked={form.permission_ids.includes(permission.id)}
                            onCheckedChange={(checked) => togglePermission(permission.id, Boolean(checked))}
                          />
                          <span>{permission.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-cyan-600 text-white hover:bg-cyan-700" disabled={isSaving}>
                {isSaving ? <FiLoader className="h-4 w-4 animate-spin" /> : <FiCheckCircle className="h-4 w-4" />}
                {editingRole ? 'Save role' : 'Create role'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </section>
  );
}
