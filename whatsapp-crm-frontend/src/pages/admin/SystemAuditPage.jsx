// src/pages/admin/SystemAuditPage.jsx
import React from 'react';
import { FiActivity, FiEdit2, FiPlusCircle, FiTrash2 } from 'react-icons/fi';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { adminApi } from '@/services/admin';
import Pager from '@/components/app/Pager';
import usePagedList from '@/lib/usePagedList';
import { formatDateTime, formatRelative } from '@/lib/format';

const ACTIONS = {
  created: { icon: FiPlusCircle, tone: 'bg-success/10 text-success' },
  updated: { icon: FiEdit2, tone: 'bg-info/10 text-info' },
  deleted: { icon: FiTrash2, tone: 'bg-destructive/10 text-destructive' },
};

// Django admin stores change messages as JSON like [{"changed": {"fields": ["Status"]}}].
function describeChange(message) {
  if (!message) return '';
  try {
    const parts = JSON.parse(message);
    if (!Array.isArray(parts)) return message;
    return parts.map((p) => {
      if (p.changed) return `Changed ${(p.changed.fields || []).join(', ').toLowerCase() || 'fields'}${p.changed.name ? ` on ${p.changed.name}` : ''}`;
      if (p.added) return p.added.name ? `Added ${p.added.name} “${p.added.object}”` : 'Created';
      if (p.deleted) return `Removed ${p.deleted.name} “${p.deleted.object}”`;
      return '';
    }).filter(Boolean).join('; ');
  } catch {
    return message;
  }
}

export function AuditList({ entries }) {
  return (
    <ul className="divide-y">
      {entries.map((e) => {
        const action = ACTIONS[e.action_label] || { icon: FiActivity, tone: 'bg-muted text-muted-foreground' };
        const Icon = action.icon;
        const model = e.content_type?.split('.')[1]?.replace(/_/g, ' ');
        return (
          <li key={e.id} className="flex items-start gap-3 px-4 py-3">
            <span className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full ${action.tone}`}><Icon className="size-4" aria-hidden /></span>
            <div className="min-w-0 flex-1">
              <p className="text-sm">
                <span className="font-medium">{e.actor || 'System'}</span> {e.action_label} {model && <span className="text-muted-foreground">{model}</span>} <span className="font-medium">“{e.object_repr}”</span>
              </p>
              {describeChange(e.change_message) && <p className="truncate text-sm text-muted-foreground">{describeChange(e.change_message)}</p>}
            </div>
            <time className="shrink-0 text-xs text-muted-foreground" dateTime={e.action_time} title={formatDateTime(e.action_time)}>{formatRelative(e.action_time)}</time>
          </li>
        );
      })}
    </ul>
  );
}

export default function SystemAuditPage() {
  const list = usePagedList((params) => adminApi.listAudit(params), []);
  const { items: entries, loading, error } = list;

  return (
    <>
      <PageHeader title="Audit log" description="Changes made through the Django admin site (records edited there bypass the dashboard’s checks)." />
      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={() => list.reload()} /> : loading ? <TableSkeleton rows={6} cols={3} /> : entries.length === 0 ? (
          <EmptyState icon={FiActivity} title="Nothing recorded yet" />
        ) : (
          <>
            <AuditList entries={entries} />
            <Pager page={list.page} pageSize={list.pageSize} count={list.count} onPage={list.setPage} noun="entry" plural="entries" />
          </>
        )}
      </div>
    </>
  );
}
