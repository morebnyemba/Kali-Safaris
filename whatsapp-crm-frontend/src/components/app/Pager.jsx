import React from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { formatNumber } from '@/lib/format';

/**
 * "1–50 of 230 bookings · Page 1 of 5  ‹ ›" footer used under every list.
 * Hidden when the list is empty. `noun` is singular; `plural` defaults to noun + "s".
 */
export default function Pager({ page, pageSize, count, onPage, noun = 'item', plural, className = '' }) {
  if (!count) return null;
  const pages = Math.max(1, Math.ceil(count / pageSize));
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, count);
  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 border-t px-4 py-2.5 text-xs text-muted-foreground ${className}`}>
      <span>
        {formatNumber(from)}–{formatNumber(to)} of {formatNumber(count)} {count === 1 ? noun : (plural || `${noun}s`)}
      </span>
      {pages > 1 && (
        <span className="flex items-center gap-1">
          <Button size="icon" variant="ghost" aria-label="Previous page" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            <FiChevronLeft />
          </Button>
          Page {page} of {pages}
          <Button size="icon" variant="ghost" aria-label="Next page" disabled={page >= pages} onClick={() => onPage(page + 1)}>
            <FiChevronRight />
          </Button>
        </span>
      )}
    </div>
  );
}
