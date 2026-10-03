import React from 'react';
import { FiAlertTriangle, FiInbox, FiLoader } from 'react-icons/fi';
import { Button } from '@/components/ui/button';

export function EmptyState({ icon: Icon = FiInbox, title, description, action, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center px-6 py-12 text-center ${className}`}>
      <span className="mb-3 flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Icon className="size-6" aria-hidden />
      </span>
      <p className="font-medium text-foreground">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ title = "Couldn't load this", message, onRetry, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center px-6 py-12 text-center ${className}`} role="alert">
      <span className="mb-3 flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <FiAlertTriangle className="size-6" aria-hidden />
      </span>
      <p className="font-medium text-foreground">{title}</p>
      {message && <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>}
      {onRetry && <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>Try again</Button>}
    </div>
  );
}

export function LoadingState({ label = 'Loading…', className = '' }) {
  return (
    <div className={`flex items-center justify-center gap-2 px-6 py-12 text-sm text-muted-foreground ${className}`}>
      <FiLoader className="size-4 animate-spin" aria-hidden /> {label}
    </div>
  );
}

/** Placeholder rows for tables while data loads. */
export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <div className="divide-y">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3">
          {Array.from({ length: cols }).map((__, c) => (
            <div key={c} className="h-4 flex-1 animate-pulse rounded bg-muted" />
          ))}
        </div>
      ))}
    </div>
  );
}
