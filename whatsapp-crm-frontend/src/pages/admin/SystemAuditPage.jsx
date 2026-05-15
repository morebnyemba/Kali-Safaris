import React from "react";
import { FiClock, FiFileText } from "react-icons/fi";

const auditRows = [
  { id: "AUD-9001", actor: "admin@kalaisafaris.com", action: "Updated role policy", when: "2026-05-15 09:41" },
  { id: "AUD-9002", actor: "ops@kalaisafaris.com", action: "Disabled user U-103", when: "2026-05-15 08:14" },
  { id: "AUD-9003", actor: "admin@kalaisafaris.com", action: "Created flow segment", when: "2026-05-14 18:33" },
];

export default function SystemAuditPage() {
  return (
    <section className="space-y-5">
      <header className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <FiFileText className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">System Audit Trail</h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">Review privileged admin operations and RBAC-sensitive updates.</p>
          </div>
        </div>
      </header>

      <div className="space-y-3">
        {auditRows.map((entry) => (
          <article key={entry.id} className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.id}</h2>
              <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-300"><FiClock className="h-3.5 w-3.5" />{entry.when}</span>
            </div>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300"><span className="font-medium">Actor:</span> {entry.actor}</p>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300"><span className="font-medium">Action:</span> {entry.action}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
