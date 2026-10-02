// src/components/DashboardLayout.jsx
import React, { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  FiActivity, FiBarChart2, FiCalendar, FiChevronLeft, FiChevronRight, FiClipboard, FiGitBranch,
  FiHome, FiImage, FiLogOut, FiMenu, FiMessageSquare, FiMonitor, FiMoon, FiShield, FiSun,
  FiUsers, FiX, FiSettings, FiUserCheck, FiList,
} from 'react-icons/fi';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { useAuth } from '@/context/AuthContext';
import { BRAND_ATTRIBUTION } from '@/config/appConfig';
import { APP_ROLES, getRoleFromUser } from '@/lib/rbac';
import { useTheme } from '@/lib/theme';
import InitialsAvatar from './app/InitialsAvatar';

const NAV_GROUPS = [
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
      { to: '/conversation', label: 'Inbox', icon: FiMessageSquare },
      { to: '/bookings', label: 'Bookings', icon: FiCalendar },
      { to: '/inquiries', label: 'Tour inquiries', icon: FiClipboard },
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
    label: 'Settings',
    items: [
      { to: '/api-settings', label: 'WhatsApp API', icon: FiSettings },
      { to: '/admin', label: 'Admin center', icon: FiShield, end: true, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
      { to: '/admin/users', label: 'Users', icon: FiUserCheck, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
      { to: '/admin/roles', label: 'Roles', icon: FiList, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
      { to: '/admin/audit', label: 'Audit log', icon: FiActivity, roles: [APP_ROLES.ADMIN, APP_ROLES.MANAGER] },
    ],
  },
];

// Longest prefix wins, so /admin/users beats /admin and /flows/edit/3 maps to Flows.
const PAGE_TITLES = [
  ['/flows/new', 'New flow', 'Automation'],
  ['/flows/edit', 'Edit flow', 'Automation'],
  ...NAV_GROUPS.flatMap((g) => g.items.map((i) => [i.to, i.label, g.label])),
].sort((a, b) => b[0].length - a[0].length);

const ROLE_LABEL = { [APP_ROLES.ADMIN]: 'Administrator', [APP_ROLES.MANAGER]: 'Manager', [APP_ROLES.AGENT]: 'Agent' };
const THEME_OPTIONS = [
  { value: 'light', label: 'Light', icon: FiSun },
  { value: 'dark', label: 'Dark', icon: FiMoon },
  { value: 'system', label: 'System', icon: FiMonitor },
];

function BrandMark({ collapsed }) {
  return (
    <Link to="/dashboard" className="flex min-w-0 items-center gap-2.5" aria-label="Kalai Safaris dashboard">
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

function SidebarNav({ collapsed, role, onNavigate }) {
  return (
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4" aria-label="Main">
      {NAV_GROUPS.map((group) => {
        const items = group.items.filter((item) => !item.roles || item.roles.includes(role));
        if (items.length === 0) return null;
        return (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/45">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {items.map(({ to, label, icon: Icon, end }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={end}
                    onClick={onNavigate}
                    title={collapsed ? label : undefined}
                    className={({ isActive }) => [
                      'group flex h-9 items-center gap-3 rounded-md px-2.5 text-sm font-medium transition-colors',
                      collapsed ? 'justify-center' : '',
                      isActive
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_3px_0_0_var(--sidebar-primary)]'
                        : 'text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground',
                    ].join(' ')}
                  >
                    <Icon className="size-[18px] shrink-0" aria-hidden />
                    {!collapsed && <span className="truncate">{label}</span>}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </nav>
  );
}

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { mode, setMode } = useTheme();
  const role = getRoleFromUser(user);
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebarCollapsed') === 'true'; } catch { return false; }
  });
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    try { localStorage.setItem('sidebarCollapsed', String(collapsed)); } catch { /* ignore */ }
  }, [collapsed]);

  useEffect(() => setMobileOpen(false), [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const [, pageTitle = 'Dashboard', section = 'Overview'] = PAGE_TITLES.find(([prefix]) => location.pathname.startsWith(prefix)) || [];

  useEffect(() => {
    document.title = `${pageTitle} · Kalai Safaris`;
  }, [pageTitle]);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const ThemeIcon = THEME_OPTIONS.find((o) => o.value === mode)?.icon || FiMonitor;
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || 'User';

  return (
    <div className="flex min-h-dvh bg-background text-foreground">
      {/* Desktop sidebar */}
      <aside
        className={`sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 md:flex ${collapsed ? 'w-[68px]' : 'w-60'}`}
      >
        <div className={`flex h-16 items-center border-b border-sidebar-border px-3 ${collapsed ? 'justify-center' : 'justify-between'}`}>
          <BrandMark collapsed={collapsed} />
        </div>
        <SidebarNav collapsed={collapsed} role={role} />
        <div className="border-t border-sidebar-border p-3">
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className={`flex h-9 w-full items-center gap-3 rounded-md px-2.5 text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground ${collapsed ? 'justify-center' : ''}`}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <FiChevronRight className="size-[18px]" /> : <><FiChevronLeft className="size-[18px]" /> Collapse</>}
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative flex h-full w-72 max-w-[85%] flex-col bg-sidebar shadow-xl">
            <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-3">
              <BrandMark />
              <button type="button" onClick={() => setMobileOpen(false)} className="rounded-md p-2 text-sidebar-foreground/80 hover:bg-sidebar-accent" aria-label="Close menu">
                <FiX className="size-5" />
              </button>
            </div>
            <SidebarNav role={role} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b bg-background/85 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70 sm:px-6">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <FiMenu className="size-5" />
          </Button>
          {/* Breadcrumb: each page renders its own heading, so the bar stays quiet. */}
          <p className="min-w-0 flex-1 truncate text-sm">
            <span className="text-muted-foreground">{section}</span>
            <span className="px-1.5 text-muted-foreground/60" aria-hidden>/</span>
            <span className="font-medium text-foreground">{pageTitle}</span>
          </p>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label={`Theme: ${mode}`}>
                <ThemeIcon className="size-[18px]" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Appearance</DropdownMenuLabel>
              {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
                <DropdownMenuItem key={value} onClick={() => setMode(value)} className={mode === value ? 'font-semibold' : ''}>
                  <Icon className="size-4" /> {label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button type="button" className="flex items-center gap-2.5 rounded-full py-1 pl-1 pr-1 hover:bg-accent sm:pr-3" aria-label="Account menu">
                <InitialsAvatar name={displayName} size="sm" />
                <span className="hidden text-left leading-tight sm:block">
                  <span className="block text-sm font-medium">{displayName}</span>
                  <span className="block text-xs text-muted-foreground">{ROLE_LABEL[role]}</span>
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="font-normal">
                <span className="block text-sm font-medium">{displayName}</span>
                <span className="block text-xs text-muted-foreground">{user?.username} · {ROLE_LABEL[role]}</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                <FiLogOut className="size-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-7xl">
            <React.Suspense fallback={<LayoutSkeleton />}>
              <Outlet />
            </React.Suspense>
          </div>
        </main>

        <footer className="border-t px-4 py-3 text-center text-xs text-muted-foreground sm:px-6">
          Kalai Safaris operations console ·{' '}
          <a href={BRAND_ATTRIBUTION.url} target="_blank" rel="noopener noreferrer" className="hover:text-foreground hover:underline">
            {BRAND_ATTRIBUTION.text}
          </a>
        </footer>
      </div>
    </div>
  );
}

const LayoutSkeleton = () => (
  <div className="space-y-6">
    <Skeleton className="h-8 w-48" />
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28 w-full rounded-xl" />)}
    </div>
    <Skeleton className="h-80 w-full rounded-xl" />
  </div>
);
