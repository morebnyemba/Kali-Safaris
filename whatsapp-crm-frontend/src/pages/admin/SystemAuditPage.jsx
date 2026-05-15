import React, { useEffect, useState } from "react";
import { FiClock, FiFileText, FiLoader } from "react-icons/fi";
import { adminApi } from '@/services/admin';

export default function SystemAuditPage() {
  const [entries, setEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAudit() {
      setIsLoading(true);
      try {
        const response = await adminApi.listAudit();
        setEntries(response.results);
      } finally {
        setIsLoading(false);
      }
    }

    loadAudit();
  }, []);

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
        {isLoading ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
            <FiLoader className="mx-auto mb-2 h-5 w-5 animate-spin" />
            Loading audit trail...
          </div>
        ) : entries.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
            No audit entries are available yet.
          </div>
        ) : entries.map((entry) => (
          <article key={entry.id} className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">#{entry.id} · {entry.object_repr}</h2>
              <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-300"><FiClock className="h-3.5 w-3.5" />{new Date(entry.action_time).toLocaleString()}</span>
            </div>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300"><span className="font-medium">Actor:</span> {entry.actor || 'system'}</p>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300"><span className="font-medium">Action:</span> {entry.action_label} {entry.content_type ? `on ${entry.content_type}` : ''}</p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{entry.change_message || 'No change message recorded.'}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
