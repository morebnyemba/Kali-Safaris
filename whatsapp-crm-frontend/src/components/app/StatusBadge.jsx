import React from 'react';

const TONE_CLASSES = {
  neutral: 'bg-muted text-muted-foreground',
  success: 'bg-success/12 text-success',
  warning: 'bg-warning/18 text-[color-mix(in_oklch,var(--warning)_70%,black)] dark:text-warning',
  danger: 'bg-destructive/10 text-destructive',
  info: 'bg-info/10 text-info',
  accent: 'bg-brand-accent/12 text-brand-accent',
};

// Booking payment statuses and inquiry statuses → tone + label.
const STATUS = {
  paid: ['success', 'Paid'],
  deposit_paid: ['info', 'Deposit paid'],
  awaiting_details: ['warning', 'Awaiting passenger details'],
  pending: ['neutral', 'Pending payment'],
  pending_manual: ['warning', 'Manual verification'],
  refunded: ['neutral', 'Refunded'],
  cancelled: ['danger', 'Cancelled'],
  new: ['accent', 'New'],
  contacted: ['info', 'Contacted'],
  proposal_sent: ['warning', 'Proposal sent'],
  converted: ['success', 'Converted'],
  closed: ['neutral', 'Closed'],
  active: ['success', 'Active'],
  inactive: ['neutral', 'Inactive'],
  synced: ['success', 'Synced to WhatsApp'],
  local: ['neutral', 'Not synced yet'],
  uploading: ['info', 'Uploading…'],
  error_upload: ['danger', 'Upload failed'],
  expired: ['warning', 'Needs re-sync'],
  error_resync: ['danger', 'Re-sync failed'],
  failed: ['danger', 'Failed'],
};

export default function StatusBadge({ status, label, tone, className = '' }) {
  const [defaultTone, defaultLabel] = STATUS[status] || ['neutral', status];
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${TONE_CLASSES[tone || defaultTone]} ${className}`}
    >
      {label || defaultLabel || '—'}
    </span>
  );
}
