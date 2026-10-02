import React from 'react';
import { Link } from 'react-router-dom';

const TONES = {
  default: 'text-primary bg-primary/10',
  accent: 'text-brand-accent bg-brand-accent/10',
  warning: 'text-warning bg-warning/15',
  danger: 'text-destructive bg-destructive/10',
  info: 'text-info bg-info/10',
};

/** KPI tile. `to` makes the whole tile a link. */
export default function StatCard({ label, value, hint, icon: Icon, tone = 'default', to, loading }) {
  const body = (
    <div className="flex h-full items-start justify-between gap-3 rounded-xl border bg-card p-4 shadow-xs transition-colors hover:border-primary/30">
      <div className="min-w-0">
        <p className="text-sm text-muted-foreground">{label}</p>
        {loading ? (
          <div className="mt-2 h-7 w-16 animate-pulse rounded bg-muted" />
        ) : (
          <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
        )}
        {hint && <p className="mt-1 truncate text-xs text-muted-foreground">{hint}</p>}
      </div>
      {Icon && (
        <span className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${TONES[tone] || TONES.default}`}>
          <Icon className="size-[18px]" aria-hidden />
        </span>
      )}
    </div>
  );
  return to ? (
    <Link to={to} className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
      {body}
    </Link>
  ) : body;
}
