import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FiShield, FiUsers, FiLock, FiDatabase, FiLoader } from "react-icons/fi";
import { adminApi } from '@/services/admin';

const adminModules = [
  {
    title: "User Management",
    description: "Create, update, deactivate, and review platform user accounts.",
    to: "/admin/users",
    icon: <FiUsers className="h-5 w-5" />,
    key: 'users',
  },
  {
    title: "Roles & RBAC",
    description: "Manage role definitions, role assignments, and permission policy.",
    to: "/admin/roles",
    icon: <FiLock className="h-5 w-5" />,
    key: 'roles',
  },
  {
    title: "System Audit",
    description: "Track sensitive actions and inspect admin event history.",
    to: "/admin/audit",
    icon: <FiDatabase className="h-5 w-5" />,
    key: 'audit',
  },
];

export default function AdminOverviewPage() {
  const [summary, setSummary] = useState({ users: 0, roles: 0, audit: 0 });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadSummary() {
      setIsLoading(true);
      try {
        const [users, roles, audit] = await Promise.all([
          adminApi.listUsers({ page: 1 }),
          adminApi.listRoles({ page: 1 }),
          adminApi.listAudit({ page: 1 }),
        ]);

        setSummary({
          users: users.count,
          roles: roles.count,
          audit: audit.count,
        });
      } finally {
        setIsLoading(false);
      }
    }

    loadSummary();
  }, []);

  return (
    <section className="space-y-6">
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <FiShield className="h-7 w-7 text-cyan-600 dark:text-cyan-400" />
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Admin Control Center</h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">Centralized controls for CRUD operations, role access, and compliance logging.</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {adminModules.map((module) => (
          <Link
            key={module.to}
            to={module.to}
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-cyan-400 hover:shadow-md dark:border-slate-700 dark:bg-slate-900"
          >
            <div className="mb-3 inline-flex rounded-lg bg-cyan-100 p-2 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300">
              {module.icon}
            </div>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{module.title}</h2>
              <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                {isLoading ? <FiLoader className="h-3.5 w-3.5 animate-spin" /> : summary[module.key]}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{module.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
