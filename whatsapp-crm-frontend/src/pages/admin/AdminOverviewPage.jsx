import React from "react";
import { Link } from "react-router-dom";
import { FiShield, FiUsers, FiLock, FiDatabase } from "react-icons/fi";

const adminModules = [
  {
    title: "User Management",
    description: "Create, update, deactivate, and review platform user accounts.",
    to: "/admin/users",
    icon: <FiUsers className="h-5 w-5" />,
  },
  {
    title: "Roles & RBAC",
    description: "Manage role definitions, role assignments, and permission policy.",
    to: "/admin/roles",
    icon: <FiLock className="h-5 w-5" />,
  },
  {
    title: "System Audit",
    description: "Track sensitive actions and inspect admin event history.",
    to: "/admin/audit",
    icon: <FiDatabase className="h-5 w-5" />,
  },
];

export default function AdminOverviewPage() {
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
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{module.title}</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{module.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
