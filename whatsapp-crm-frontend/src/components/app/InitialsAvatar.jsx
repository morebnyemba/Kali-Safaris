import React from 'react';

// Rendered locally: never send customer names to a third-party avatar service.
const HUES = [155, 45, 230, 300, 85, 190, 20];

const initialsOf = (name = '') => {
  const parts = String(name).trim().split(/[\s._-]+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

export default function InitialsAvatar({ name, size = 'md', className = '' }) {
  const text = String(name || '');
  const hue = HUES[[...text].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % HUES.length];
  const sizes = { sm: 'size-8 text-xs', md: 'size-10 text-sm', lg: 'size-14 text-lg' };
  return (
    <span
      aria-hidden
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-semibold ${sizes[size] || sizes.md} ${className}`}
      style={{ background: `oklch(0.93 0.04 ${hue})`, color: `oklch(0.38 0.09 ${hue})` }}
    >
      {initialsOf(text)}
    </span>
  );
}
