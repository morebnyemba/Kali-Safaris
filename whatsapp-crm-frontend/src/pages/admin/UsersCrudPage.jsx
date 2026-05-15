import React from "react";
import { FiPlus, FiEdit2, FiUserX, FiRefreshCw } from "react-icons/fi";
import { Button } from "@/components/ui/button";

const sampleUsers = [
  { id: "U-101", name: "Admin User", email: "admin@kalaisafaris.com", role: "admin", status: "active" },
  { id: "U-102", name: "Ops Manager", email: "ops@kalaisafaris.com", role: "manager", status: "active" },
  { id: "U-103", name: "Support Agent", email: "agent@kalaisafaris.com", role: "agent", status: "inactive" },
];

export default function UsersCrudPage() {
  return (
    <section className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Users CRUD</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">Create, update, and disable frontend admin users.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2"><FiRefreshCw className="h-4 w-4" />Refresh</Button>
          <Button className="gap-2 bg-cyan-600 text-white hover:bg-cyan-700"><FiPlus className="h-4 w-4" />New user</Button>
        </div>
      </header>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
          <thead className="bg-slate-50 dark:bg-slate-800/70">
            <tr>
              {[
                "User ID",
                "Name",
                "Email",
                "Role",
                "Status",
                "Actions",
              ].map((col) => (
                <th key={col} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {sampleUsers.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">{user.id}</td>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">{user.name}</td>
                <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">{user.email}</td>
                <td className="px-4 py-3 text-sm capitalize text-slate-700 dark:text-slate-200">{user.role}</td>
                <td className="px-4 py-3 text-sm capitalize text-slate-700 dark:text-slate-200">{user.status}</td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" className="gap-1"><FiEdit2 className="h-3.5 w-3.5" />Edit</Button>
                    <Button size="sm" variant="destructive" className="gap-1"><FiUserX className="h-3.5 w-3.5" />Disable</Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
