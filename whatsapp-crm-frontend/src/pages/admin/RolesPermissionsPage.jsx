import React from "react";
import { FiKey, FiLock } from "react-icons/fi";
import { Button } from "@/components/ui/button";

const roleRows = [
  { role: "admin", canManageUsers: true, canEditFlows: true, canViewAudit: true },
  { role: "manager", canManageUsers: false, canEditFlows: true, canViewAudit: true },
  { role: "agent", canManageUsers: false, canEditFlows: false, canViewAudit: false },
];

export default function RolesPermissionsPage() {
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

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
          <thead className="bg-slate-50 dark:bg-slate-800/70">
            <tr>
              {["Role", "Manage Users", "Edit Flows", "View Audit", "Action"].map((col) => (
                <th key={col} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {roleRows.map((row) => (
              <tr key={row.role}>
                <td className="px-4 py-3 text-sm font-medium capitalize text-slate-800 dark:text-slate-100">{row.role}</td>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{row.canManageUsers ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{row.canEditFlows ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{row.canViewAudit ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-sm">
                  <Button size="sm" variant="outline" className="gap-1"><FiKey className="h-3.5 w-3.5" />Edit Policy</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
