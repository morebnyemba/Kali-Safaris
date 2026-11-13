// src/components/DashboardLayout.jsx
import React, { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  FiChevronsLeft, FiChevronsRight, FiLogOut, FiMenu, FiMonitor, FiMoon, FiSun, FiX,
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
import { BrandMark, NAV_GROUPS, SidebarNav, useNavCounts } from './app/Sidebar';

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

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { mode, setMode } = useTheme();
  const role = getRoleFromUser(user);
  // A saved choice wins; otherwise tablets (768–1023px) start on the icon rail so the page keeps its width.
  const [collapsed, setCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem('sidebarCollapsed');
      if (saved !== null) return saved === 'true';
    } catch { /* ignore */ }
    return typeof window !== 'undefined' && window.innerWidth < 1024;
  });
  const userToggled = useRef(false);
  const toggleCollapsed = () => { userToggled.current = true; setCollapsed((c) => !c); };
  const counts = useNavCounts();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!userToggled.current) return; // don't freeze the screen-size default into a preference
    try { localStorage.setItem('sidebarCollapsed', String(collapsed)); } catch { /* ignore */ }
  }, [collapsed]);

  // Ctrl/⌘ + B toggles the sidebar (not while typing).
  useEffect(() => {
    const onKey = (e) => {
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey || e.key.toLowerCase() !== 'b') return;
      const t = e.target;
      if (t instanceof HTMLElement && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      e.preventDefault();
      if (window.matchMedia('(min-width: 768px)').matches) toggleCollapsed();
      else setMobileOpen((o) => !o);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => setMobileOpen(false), [location.pathname]);

  const menuButtonRef = useRef(null);
  const closeButtonRef = useRef(null);
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  // Drawer behaves like a modal: Escape closes it, focus moves in and comes back,
  // and widening to desktop closes it (otherwise the body scroll lock stays on
  // behind the now-hidden drawer and the page can't scroll).
  useEffect(() => {
    if (!mobileOpen) return undefined;
    const opener = menuButtonRef.current;
    closeButtonRef.current?.focus();
    const onKey = (e) => { if (e.key === 'Escape') setMobileOpen(false); };
    const desktop = window.matchMedia('(min-width: 768px)');
    const onWide = (e) => { if (e.matches) setMobileOpen(false); };
    document.addEventListener('keydown', onKey);
    desktop.addEventListener('change', onWide);
    return () => {
      document.removeEventListener('keydown', onKey);
      desktop.removeEventListener('change', onWide);
      if (opener && opener.offsetParent !== null) opener.focus();
    };
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
        <SidebarNav collapsed={collapsed} role={role} counts={counts} />
        <div className={`border-t border-sidebar-border ${collapsed ? 'p-2.5' : 'p-3'}`}>
          <button
            type="button"
            onClick={toggleCollapsed}
            title={collapsed ? 'Expand sidebar (Ctrl+B)' : undefined}
            className={`flex h-9 w-full items-center gap-3 rounded-md px-2.5 text-sm text-sidebar-foreground/70 outline-none hover:bg-white/[0.06] hover:text-sidebar-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring ${collapsed ? 'justify-center px-0' : ''}`}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-keyshortcuts="Control+B Meta+B"
          >
            {collapsed ? <FiChevronsRight className="size-[18px]" /> : (
              <>
                <FiChevronsLeft className="size-[18px]" /> Collapse
                <kbd className="ml-auto rounded border border-sidebar-border px-1.5 py-0.5 font-sans text-[10px] text-sidebar-foreground/50">Ctrl B</kbd>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="absolute inset-0 bg-black/50 animate-in fade-in-0" onClick={() => setMobileOpen(false)} />
          <aside className="relative flex h-full w-72 max-w-[85%] flex-col bg-sidebar shadow-xl animate-in slide-in-from-left duration-200">
            <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-3">
              <BrandMark />
              <button ref={closeButtonRef} type="button" onClick={() => setMobileOpen(false)} className="rounded-md p-2 text-sidebar-foreground/80 hover:bg-sidebar-accent" aria-label="Close menu">
                <FiX className="size-5" />
              </button>
            </div>
            <SidebarNav role={role} counts={counts} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b bg-background/85 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70 sm:px-6">
          <Button ref={menuButtonRef} variant="ghost" size="icon" className="md:hidden" aria-expanded={mobileOpen} onClick={() => setMobileOpen(true)} aria-label="Open menu">
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
