// src/components/app/Sidebar.jsx
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import {
  FiActivity, FiBarChart2, FiCalendar, FiChevronDown, FiClipboard, FiCreditCard, FiGitBranch, FiGlobe,
  FiHome, FiImage, FiList, FiMessageSquare, FiSettings, FiShield, FiUserCheck, FiUsers,
} from 'react-icons/fi';
import apiClient from '@/lib/api';
import { APP_ROLES } from '@/lib/rbac';

/**
 * `badge(counts)` returns { count, hint } for the live counter next to an item:
 * things that need a person now. Counts match the filter each page opens with.
 */
export const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: FiHome },
      { to: '/analytics', label: 'Analytics', icon: FiBarChart2 },
    ],
  },
  {
    label: 'Operations',
    items: [
      {
        to: '/conversation', label: 'Inbox', icon: FiMessageSquare,
        badge: (c) => ({ count: c.inbox_attention, hint: 'waiting for a person' }),
      },
      {
        to: '/bookings', label: 'Bookings', icon: FiCalendar,
        badge: (c) => ({
          count: (c.bookings_on_hold || 0) + (c.bookings_awaiting_details || 0),
          hint: `${c.bookings_on_hold || 0} on hold · ${c.bookings_awaiting_details || 0} awaiting passenger details`,
        }),
      },
      {
        to: '/payments', label: 'Payments', icon: FiCreditCard,
        badge: (c) => ({ count: c.payments_pending, hint: 'awaiting verification' }),
      },
      {
        to: '/inquiries', label: 'Tour inquiries', icon: FiClipboard,
        badge: (c) => ({ count: c.inquiries_new, hint: 'new' }),
      },
      { to: '/contacts', label: 'Contacts', icon: FiUsers },
    ],
  },
  {
    label: 'Automation',
    items: [
      { to: '/flows', label: 'Flows', icon: FiGitBranch },
      { to: '/media-library', label: 'Media library', icon: FiImage },
    ],
  },
  {
    label: 'Website',
    items: [
      { to: '/website-gallery', label: 'Gallery', icon: FiGlobe },
    ],
  },
  {
    label: 'Settings',
    collapsible: true, // folded by default: used rarely, and it pushed the list past a laptop screen
    items: [
      { to: '/api-settings', label: 'WhatsApp API', icon: FiSettings, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
      { to: '/admin', label: 'Admin center', icon: FiShield, end: true, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
      { to: '/admin/users', label: 'Users', icon: FiUserCheck, roles: [APP_ROLES.ADMIN] },
      { to: '/admin/roles', label: 'Roles', icon: FiList, roles: [APP_ROLES.ADMIN] },
      { to: '/admin/audit', label: 'Audit log', icon: FiActivity, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
    ],
  },
];

const POLL_MS = 60_000;

/** Live badge counts: on load, every minute while the tab is visible, and on each page change. */
export function useNavCounts() {
  const [counts, setCounts] = useState({});
  const location = useLocation();
  const lastFetch = useRef(0);

  const refresh = useCallback(async (force = false) => {
    if (!force && Date.now() - lastFetch.current < 10_000) return; // route hops in quick succession
    lastFetch.current = Date.now();
    try {
      const res = await apiClient.get('/crm-api/stats/nav-counts/', { suppressErrorToast: true });
      setCounts(res.data || {});
    } catch {
      // Badges are a hint; never surface an error for them.
    }
  }, []);

  useEffect(() => { refresh(); }, [location.pathname, refresh]);

  useEffect(() => {
    const tick = () => { if (document.visibilityState === 'visible') refresh(true); };
    const id = window.setInterval(tick, POLL_MS);
    document.addEventListener('visibilitychange', tick);
    window.addEventListener('nav-counts:refresh', tick); // pages can ask after approving a payment etc.
    return () => {
      window.clearInterval(id);
      document.removeEventListener('visibilitychange', tick);
      window.removeEventListener('nav-counts:refresh', tick);
    };
  }, [refresh]);

  return counts;
}

function readOpenGroups() {
  try { return JSON.parse(localStorage.getItem('sidebarGroups') || '{}') || {}; } catch { return {}; }
}

function isActivePath(pathname, item) {
  return item.end ? pathname === item.to : pathname === item.to || pathname.startsWith(`${item.to}/`);
}

function Badge({ count, collapsed }) {
  if (!count) return null;
  const text = collapsed ? (count > 9 ? '9+' : String(count)) : (count > 99 ? '99+' : String(count));
  if (collapsed) {
    return (
      <span className="absolute -right-3 -top-2 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-sidebar-primary px-[3px] text-[9px] font-bold leading-none tabular-nums text-sidebar-primary-foreground ring-2 ring-sidebar">
        {text}
      </span>
    );
  }
  return (
    <span className="ml-auto rounded-full bg-sidebar-primary px-1.5 py-0.5 text-[11px] font-semibold leading-none tabular-nums text-sidebar-primary-foreground">
      {text}
    </span>
  );
}

export function BrandMark({ collapsed }) {
  return (
    <Link to="/dashboard" className="flex min-w-0 items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring" aria-label="Kalai Safaris dashboard">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-accent text-base font-bold text-white shadow-sm">
        K
      </span>
      {!collapsed && (
        <span className="min-w-0 leading-tight">
          <span className="block truncate text-sm font-semibold text-sidebar-foreground">Kalai Safaris</span>
          <span className="block truncate text-[11px] text-sidebar-foreground/60">Operations console</span>
        </span>
      )}
    </Link>
  );
}

export function SidebarNav({ collapsed = false, role, counts = {}, onNavigate }) {
  const { pathname } = useLocation();
  const navRef = useRef(null);
  const [openGroups, setOpenGroups] = useState(readOpenGroups);
  const [tip, setTip] = useState(null); // collapsed rail: { label, hint, top }
  const [fade, setFade] = useState({ top: false, bottom: false });

  useEffect(() => {
    try { localStorage.setItem('sidebarGroups', JSON.stringify(openGroups)); } catch { /* ignore */ }
  }, [openGroups]);

  const updateFade = useCallback(() => {
    const el = navRef.current;
    if (!el) return;
    setFade({ top: el.scrollTop > 4, bottom: el.scrollTop + el.clientHeight < el.scrollHeight - 4 });
  }, []);

  // Keep the current page's link in view (deep links into Settings on a short screen).
  useLayoutEffect(() => {
    navRef.current?.querySelector('[aria-current="page"]')?.scrollIntoView({ block: 'nearest' });
    updateFade();
  }, [pathname, collapsed, openGroups, updateFade]);

  useEffect(() => {
    window.addEventListener('resize', updateFade);
    return () => window.removeEventListener('resize', updateFade);
  }, [updateFade]);

  useEffect(() => { setTip(null); }, [pathname, collapsed]);

  const showTip = (e, label, hint) => {
    if (!collapsed) return;
    const r = e.currentTarget.getBoundingClientRect();
    setTip({ label, hint, top: r.top + r.height / 2, left: r.right + 10 });
  };

  const mask = fade.top && fade.bottom
    ? 'linear-gradient(to bottom, transparent, #000 24px, #000 calc(100% - 24px), transparent)'
    : fade.top ? 'linear-gradient(to bottom, transparent, #000 24px)'
      : fade.bottom ? 'linear-gradient(to bottom, #000 calc(100% - 24px), transparent)' : undefined;

  return (
    <>
      <nav
        ref={navRef}
        onScroll={() => { updateFade(); setTip(null); }}
        className={`sidebar-scroll flex-1 overflow-y-auto overscroll-contain py-3 ${collapsed ? 'px-2.5' : 'px-3'}`}
        style={mask ? { maskImage: mask, WebkitMaskImage: mask } : undefined}
        aria-label="Main"
      >
        {NAV_GROUPS.map((group, gi) => {
          const items = group.items.filter((item) => !item.roles || item.roles.includes(role));
          if (items.length === 0) return null;
          const hasActive = items.some((item) => isActivePath(pathname, item));
          const groupCount = items.reduce((n, item) => n + (item.badge?.(counts).count || 0), 0);
          // A folded group still opens when you're on one of its pages.
          const open = collapsed || !group.collapsible || hasActive || openGroups[group.label] === true;
          const listId = `nav-group-${gi}`;
          return (
            <div key={group.label} className={gi === 0 ? '' : collapsed ? 'mt-2 border-t border-sidebar-border pt-2' : 'mt-4'}>
              {!collapsed && (group.collapsible ? (
                <button
                  type="button"
                  onClick={() => setOpenGroups((g) => ({ ...g, [group.label]: !open }))}
                  disabled={hasActive}
                  aria-expanded={open}
                  aria-controls={listId}
                  className="mb-1 flex w-full items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/45 hover:text-sidebar-foreground/80 disabled:cursor-default disabled:hover:text-sidebar-foreground/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
                >
                  {group.label}
                  {!open && groupCount > 0 && <span className="ml-1 size-1.5 rounded-full bg-sidebar-primary" aria-hidden />}
                  <FiChevronDown className={`ml-auto size-3.5 transition-transform ${open ? '' : '-rotate-90'}`} aria-hidden />
                </button>
              ) : (
                <p className="mb-1 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/45">{group.label}</p>
              ))}
              {open && (
                <ul id={listId} className="space-y-0.5">
                  {items.map((item) => {
                    const { to, label, icon: Icon, end } = item;
                    const badge = item.badge?.(counts) || {};
                    const hint = badge.count ? `${badge.count} ${badge.hint}` : '';
                    return (
                      <li key={to}>
                        <NavLink
                          to={to}
                          end={end}
                          onClick={onNavigate}
                          onMouseEnter={(e) => showTip(e, label, hint)}
                          onMouseLeave={() => setTip(null)}
                          onFocus={(e) => showTip(e, label, hint)}
                          onBlur={() => setTip(null)}
                          aria-label={collapsed ? (hint ? `${label}, ${hint}` : label) : undefined}
                          title={!collapsed && hint ? hint : undefined}
                          className={({ isActive }) => [
                            'relative flex h-9 items-center gap-3 rounded-md text-sm font-medium outline-none transition-colors',
                            'focus-visible:ring-2 focus-visible:ring-sidebar-ring',
                            collapsed ? 'justify-center px-0' : 'px-2.5',
                            isActive
                              ? 'bg-sidebar-accent text-sidebar-accent-foreground before:absolute before:inset-y-1.5 before:-left-0.5 before:w-[3px] before:rounded-full before:bg-sidebar-primary'
                              : 'text-sidebar-foreground/70 hover:bg-white/[0.06] hover:text-sidebar-foreground',
                          ].join(' ')}
                        >
                          {({ isActive }) => (
                            <>
                              <span className="relative flex">
                                <Icon className={`size-[18px] shrink-0 ${isActive ? 'text-sidebar-primary' : ''}`} aria-hidden />
                                {collapsed && <Badge count={badge.count} collapsed />}
                              </span>
                              {!collapsed && <span className="truncate">{label}</span>}
                              {!collapsed && <Badge count={badge.count} />}
                            </>
                          )}
                        </NavLink>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </nav>

      {/* Fixed-position tooltip for the icon rail (the nav scrolls, so an absolute one would be clipped). */}
      {collapsed && tip && (
        <div
          role="tooltip"
          className="pointer-events-none fixed z-50 -translate-y-1/2 whitespace-nowrap rounded-md bg-popover px-2.5 py-1.5 text-xs font-medium text-popover-foreground shadow-md ring-1 ring-border"
          style={{ top: tip.top, left: tip.left }}
        >
          {tip.label}
          {tip.hint && <span className="block font-normal text-muted-foreground">{tip.hint}</span>}
        </div>
      )}
    </>
  );
}
