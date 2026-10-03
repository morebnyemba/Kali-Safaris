// src/pages/admin/AdminOverviewPage.jsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiActivity, FiLock, FiSettings, FiUserCheck, FiUsers } from 'react-icons/fi';
import PageHeader from '@/components/app/PageHeader';
import StatCard from '@/components/app/StatCard';
import { EmptyState } from '@/components/app/States';
import { useAuth } from '@/context/AuthContext';
import { adminApi } from '@/services/admin';
import { metaApi } from '@/lib/api';
import { APP_ROLES, getRoleFromUser } from '@/lib/rbac';
import { AuditList } from './SystemAuditPage';

export default function AdminOverviewPage() {
  const { user } = useAuth();
  const isAdmin = getRoleFromUser(user) === APP_ROLES.ADMIN;
  const [data, setData] = useState({ users: null, active: null, roles: null, audit: [], whatsapp: undefined });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([
      adminApi.listUsers({ page_size: 100 }),
      adminApi.listRoles({ page_size: 1 }),
      adminApi.listAudit({ page_size: 6 }),
      metaApi.getConfigs(),
    ]).then(([users, roles, audit, meta]) => {
      if (cancelled) return;
      const userList = users.status === 'fulfilled' ? users.value.results : [];
      const configs = meta.status === 'fulfilled' ? (meta.value.data.results || meta.value.data || []) : null;
      setData({
        users: users.status === 'fulfilled' ? users.value.count : null,
        active: userList.filter((u) => u.is_active).length,
        roles: roles.status === 'fulfilled' ? roles.value.count : null,
        audit: audit.status === 'fulfilled' ? audit.value.results : [],
        whatsapp: configs ? configs.find((c) => c.is_active) || null : undefined,
      });
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  const wa = data.whatsapp;
  return (
    <>
      <PageHeader title="Admin center" description="Team access and system health at a glance." />
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Users" value={data.users ?? '—'} hint={data.users != null ? `${data.active} can sign in` : undefined} icon={FiUsers} to={isAdmin ? '/admin/users' : undefined} loading={loading} />
        <StatCard label="Roles" value={data.roles ?? '—'} icon={FiLock} tone="info" to={isAdmin ? '/admin/roles' : undefined} loading={loading} />
        <StatCard
          label="WhatsApp number"
          value={wa === undefined ? '—' : wa ? 'Connected' : 'Not set'}
          hint={wa ? wa.name : wa === null ? 'No active configuration' : 'Staff only'}
          icon={FiSettings}
          tone={wa === null ? 'warning' : 'accent'}
          to="/api-settings"
          loading={loading}
        />
        <StatCard label="Signed in as" value={user?.username || '—'} hint={user?.is_superuser ? 'Superuser' : getRoleFromUser(user)} icon={FiUserCheck} tone="warning" />
      </div>

      <section className="overflow-hidden rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="font-semibold">Recent admin changes</h2>
          <Link to="/admin/audit" className="text-sm text-primary hover:underline">View all</Link>
        </div>
        {data.audit.length ? <AuditList entries={data.audit} /> : <EmptyState icon={FiActivity} title={loading ? 'Loading…' : 'Nothing recorded yet'} />}
      </section>
    </>
  );
}
