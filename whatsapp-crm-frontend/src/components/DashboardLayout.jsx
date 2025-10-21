// src/components/DashboardLayout.jsx
import React, { useState, useEffect } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from './ui/tooltip';
import { useMediaQuery } from 'react-responsive';
import { useAuth } from '@/context/AuthContext';

import {
  FiSearch,
  FiSettings,
  FiMessageSquare,
  FiMenu,
  FiHome,
  FiX,
  FiChevronLeft,
  FiChevronRight,
  FiUsers,
  FiImage,
  FiUser,
  FiBell,
  FiHelpCircle,
  FiLogOut,
  FiBarChart2,
  FiCalendar,
  FiMail,
  FiActivity,
  FiCreditCard
} from 'react-icons/fi';

const DashboardBackground = () => (
  <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 overflow-hidden -z-10">
    <div
      className="absolute inset-0 opacity-10 dark:opacity-5"
      style={{
        backgroundImage: `radial-gradient(#a855f7 0.5px, transparent 0.5px)`,
        backgroundSize: '16px 16px',
      }}
    />
  </div>
);

export default function DashboardLayout() {
  const isMobile = useMediaQuery({ maxWidth: 767 });
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem('sidebarCollapsed');
      return savedState ? savedState === 'true' : isMobile;
    }
    return isMobile;
  });
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const navigationLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: <FiHome className="h-5 w-5" /> },
    { to: '/conversation', label: 'Conversations', icon: <FiMessageSquare className="h-5 w-5" /> },
    { to: '/contacts', label: 'Contacts', icon: <FiUsers className="h-5 w-5" /> },
    { to: '/installation-requests', label: 'Installation Requests', icon: <FiActivity className="h-5 w-5" /> },
    { to: '/orders', label: 'Orders', icon: <FiCreditCard className="h-5 w-5" /> },
    { to: '/site-assessments', label: 'Site Assessments', icon: <FiBarChart2 className="h-5 w-5" /> },
    { to: '/analytics', label: 'Analytics', icon: <FiBarChart2 className="h-5 w-5" /> },
    { to: '/billing', label: 'Billing', icon: <FiCreditCard className="h-5 w-5" /> },
    { to: '/media-library', label: 'Media Library', icon: <FiImage className="h-5 w-5" /> },
    { to: '/api-settings', label: 'API Settings', icon: <FiSettings className="h-5 w-5" /> },
  ];

  // Auto-collapse on mobile and expand on desktop
  useEffect(() => {
    if (isMobile) {
      setCollapsed(true);
    } else {
      setCollapsed(localStorage.getItem('sidebarCollapsed') === 'true');
    }
  }, [isMobile]);

  // Close mobile menu when resizing to desktop
  useEffect(() => {
    const handleResize = () => {
      if (!isMobile) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobile]);

  // Persist collapse state
  useEffect(() => {
    if (!isMobile) {
      localStorage.setItem('sidebarCollapsed', collapsed);
    }
  }, [collapsed, isMobile]);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  const getInitials = (name = '') => {
    if (!name) return 'U';
    const parts = name.split(/[\s._-]+/);
    if (parts.length > 1 && parts[0] && parts[1]) {
      return parts[0][0].toUpperCase() + parts[1][0].toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const userInitials = getInitials(user?.username);
  const userRole = user?.is_staff ? 'Administrator' : 'User';

  // Find the current page title from navigation links
  const currentPage = navigationLinks.find(link => location.pathname.startsWith(link.to));
  const pageTitle = currentPage ? currentPage.label : 'Dashboard';

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-slate-900 text-gray-800 dark:text-gray-200">
      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 p-4 flex items-center justify-between z-50 shadow-sm">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700"
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMobileMenuOpen ? <FiX className="h-6 w-6" /> : <FiMenu className="h-6 w-6" />}
          </Button>
          <Link to="/dashboard" className="flex items-center">
            {/* Logo removed as requested */}
          </Link>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="rounded-full relative">
            <FiBell className="h-5 w-5" />
            <span className="absolute top-0 right-0 h-2.5 w-2.5 rounded-full bg-red-500 border-2 border-white dark:border-slate-800"></span>
          </Button>
          
          <Button variant="ghost" size="icon" className="rounded-full">
            <FiUser className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm md:hidden z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative h-screen transition-all duration-300 ease-in-out border-r border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 z-50 ${
          collapsed ? 'md:w-20' : 'md:w-64'
        } ${
          isMobileMenuOpen
            ? 'translate-x-0 w-64 shadow-xl'
            : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="h-full flex flex-col">
          <div className={`flex items-center p-4 h-16 ${collapsed ? 'justify-center' : 'justify-between'}`}>
            <Link 
              to="/dashboard" 
              className={`flex items-center overflow-hidden transition-opacity duration-300 ${collapsed ? 'w-auto' : 'w-full'}`}
              onClick={() => isMobile && setIsMobileMenuOpen(false)}
            >
              {/* Logo removed as requested */}
              {!collapsed && (
                <span className="ml-3 text-lg font-semibold whitespace-nowrap">CRM Dashboard</span>
              )}
            </Link>
            {!isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCollapsed((prev) => !prev)}
                className="rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
                aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {collapsed ? <FiChevronRight className="h-5 w-5" /> : <FiChevronLeft className="h-5 w-5" />}
              </Button>
            )}
          </div>

          <TooltipProvider delayDuration={100}>
            <nav className="flex-1 overflow-y-auto py-4">
              <div className="px-3 mb-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                {!collapsed ? "Navigation" : "•"}
              </div>
              <div className="space-y-1 px-2">
                {navigationLinks.map((link) => {
                  const isActive = location.pathname === link.to;
                  
                  return (
                    <Tooltip key={link.to}>
                      <TooltipTrigger asChild>
                        <Button
                          variant={isActive ? 'secondary' : 'ghost'}
                          className={`w-full justify-start text-sm font-medium h-10 group rounded-lg relative ${
                            collapsed ? 'px-0 justify-center' : 'px-3 gap-3'
                          } ${
                            isActive
                              ? 'bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300'
                              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-700/80'
                          }`}
                          asChild
                        >
                          <Link
                            to={link.to}
                            onClick={() => isMobile && setIsMobileMenuOpen(false)}
                          >
                            <span className={`flex-shrink-0 h-5 w-5 ${
                              isActive 
                                ? 'text-purple-600 dark:text-purple-300' 
                                : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200'
                            }`}>
                              {link.icon}
                            </span>
                            {!collapsed && (
                              <span className="truncate flex-1 text-left">
                                {link.label}
                              </span>
                            )}
                            {isMobileMenuOpen && (
                              <span className="truncate flex-1 text-left ml-3">
                                {link.label}
                              </span>
                            )}
                          </Link>
                        </Button>
                      </TooltipTrigger>
                      {collapsed && !isMobileMenuOpen && (
                        <TooltipContent 
                          side="right" 
                          className="bg-gray-800 dark:bg-slate-900 text-white text-xs rounded-md px-2 py-1 shadow-lg border border-transparent dark:border-slate-700"
                        >
                          {link.label}
                        </TooltipContent>
                      )}
                    </Tooltip>
                  );
                })}
              </div>
            </nav>

            {/* Bottom section */}
            <div className="mt-auto pt-4 border-t border-gray-200 dark:border-slate-700 px-2 pb-4">
              {/* User profile */}
              <div className={`flex items-center gap-3 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-slate-700 cursor-pointer ${
                collapsed && !isMobileMenuOpen ? 'justify-center' : 'px-3'
              }`}>
                <div className="relative">
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 h-8 w-8 rounded-full flex items-center justify-center text-white font-semibold">
                    {userInitials}
                  </div>
                  <div className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-green-500 border border-white dark:border-slate-800"></div>
                </div>
                {(!collapsed || isMobileMenuOpen) && (
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{user?.username || 'User'}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{userRole}</p>
                  </div>
                )}
              </div>

              {/* Support */}
              <Button variant="ghost" className={`w-full justify-start mt-2 text-sm font-medium h-10 rounded-lg ${
                collapsed && !isMobileMenuOpen ? 'px-0 justify-center' : 'px-3 gap-3'
              }`}>
                <FiHelpCircle className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                {(isMobileMenuOpen || !collapsed) && "Help & Support"}
              </Button>

              {/* Logout */}
              <Button 
                variant="ghost" 
                className={`w-full justify-start text-sm font-medium h-10 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-700 dark:hover:text-red-300 ${
                  collapsed && !isMobileMenuOpen ? 'px-0 justify-center' : 'px-3 gap-3'
                }`}
                onClick={handleLogout}
              >
                <FiLogOut className="h-5 w-5" />
                {(isMobileMenuOpen || !collapsed) && "Logout"}
              </Button>
            </div>
          </TooltipProvider>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-screen md:pt-0 pt-16 overflow-hidden">
        {/* Desktop Header */}
        <header className="hidden md:flex items-center justify-between h-16 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 px-6">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-100">{pageTitle}</h1>
            <div className="relative max-w-md w-full">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="w-full pl-9 pr-4 py-2 rounded-md border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="rounded-full relative">
              <FiBell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 h-2.5 w-2.5 rounded-full bg-red-500 border-2 border-white dark:border-slate-800"></span>
            </Button>
            
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-purple-500 to-indigo-500 h-9 w-9 rounded-full flex items-center justify-center text-white font-semibold">
                {userInitials}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{user?.username || 'User'}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{userRole}</p>
              </div>
            </div>
          </div>
        </header>
        
        {/* Main Content */}
        <main className="flex-1 relative overflow-y-auto">
          <DashboardBackground />
          <div className="relative z-10 p-4 sm:p-6 md:p-8">
            <React.Suspense fallback={<LayoutSkeleton />}>
              <Outlet />
            </React.Suspense>
          </div>
        </main>
        
        {/* Footer */}
        <footer className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 py-4 px-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              © {new Date().getFullYear()} <a 
                href="https://pfungwa.tech" 
                target="_blank" rel="noopener noreferrer" 
                className="font-medium text-purple-600 hover:underline dark:text-purple-400"
              >Pfungwa Technologies</a>. All rights reserved.
            </div>
            <div className="flex items-center gap-4">
              <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">Terms</a>
              <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">Privacy</a>
              <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">Help Center</a>
              <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">Contact</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

const LayoutSkeleton = () => (
  <div className="space-y-6 p-1 animate-pulse">
    <div className="flex justify-between items-center">
      <Skeleton className="h-8 w-48 rounded-lg bg-gray-200 dark:bg-slate-700" />
      <Skeleton className="h-10 w-32 rounded-lg bg-gray-200 dark:bg-slate-700" />
    </div>
    <Skeleton className="h-6 w-2/3 rounded-lg bg-gray-200 dark:bg-slate-700" />
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-40 w-full rounded-xl bg-gray-200 dark:bg-slate-700" />
      ))}
    </div>
    <Skeleton className="h-96 w-full rounded-xl bg-gray-200 dark:bg-slate-700" />
  </div>
);