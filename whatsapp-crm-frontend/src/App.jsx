// Filename: src/App.jsx
import React, { lazy } from 'react';
import { RouterProvider, createBrowserRouter, Navigate, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './components/DashboardLayout';
import RoleRoute from './components/RoleRoute';
import LoginPage from './pages/LoginPage';
import { APP_ROLES } from './lib/rbac';

// Pages are split per route so charts, the flow editor, etc. only load when opened.
// DashboardLayout wraps <Outlet /> in <Suspense>.
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const ApiSettings = lazy(() => import('./pages/ApiSettings'));
const FlowsPage = lazy(() => import('./pages/FlowsPage'));
const FlowEditorPage = lazy(() => import('./pages/FlowEditorPage'));
const MediaLibraryPage = lazy(() => import('./pages/MediaLibraryPage'));
const ContactsPage = lazy(() => import('./pages/ContactsPage'));
const Conversation = lazy(() => import('./pages/Conversation'));
const BookingsPage = lazy(() => import('./pages/BookingsPage'));
const InquiriesPage = lazy(() => import('./pages/InquiriesPage'));
const AdminOverviewPage = lazy(() => import('./pages/admin/AdminOverviewPage'));
const UsersCrudPage = lazy(() => import('./pages/admin/UsersCrudPage'));
const RolesPermissionsPage = lazy(() => import('./pages/admin/RolesPermissionsPage'));
const SystemAuditPage = lazy(() => import('./pages/admin/SystemAuditPage'));

const NotFoundPage = () => (
  <div className="flex flex-col items-center justify-center py-24 text-center">
    <p className="text-sm font-semibold text-brand-accent">404</p>
    <h1 className="mt-2 text-2xl font-semibold">Page not found</h1>
    <p className="mt-2 text-muted-foreground">That page doesn't exist or has moved.</p>
    <Link to="/dashboard" className="mt-6 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90">
      Back to dashboard
    </Link>
  </div>
);

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      {
        path: 'api-settings',
        element: (
          <RoleRoute requiredRoles={[APP_ROLES.ADMIN, APP_ROLES.MANAGER]}>
            <ApiSettings />
          </RoleRoute>
        ),
      },
      
      // Flow Management
      { path: 'flows', element: <FlowsPage /> }, // Page to list all flows
      { path: 'flows/new', element: <FlowEditorPage /> },
      { path: 'flows/edit/:flowId', element: <FlowEditorPage /> },
      
  // Other sections
  { path: 'media-library', element: <MediaLibraryPage /> },
  { path: 'contacts', element: <ContactsPage /> },
  { path: 'analytics', element: <AnalyticsPage />},
  { path: 'bookings', element: <BookingsPage /> },
  { path: 'inquiries', element: <InquiriesPage /> },

  // Admin and RBAC
  {
    path: 'admin',
    element: (
      <RoleRoute requiredRoles={[APP_ROLES.ADMIN, APP_ROLES.MANAGER]}>
        <AdminOverviewPage />
      </RoleRoute>
    )
  },
  {
    path: 'admin/users',
    element: (
      <RoleRoute requiredRoles={[APP_ROLES.ADMIN]}>
        <UsersCrudPage />
      </RoleRoute>
    )
  },
  {
    path: 'admin/roles',
    element: (
      <RoleRoute requiredRoles={[APP_ROLES.ADMIN]}>
        <RolesPermissionsPage />
      </RoleRoute>
    )
  },
  {
    path: 'admin/audit',
    element: (
      <RoleRoute requiredRoles={[APP_ROLES.ADMIN, APP_ROLES.MANAGER]}>
        <SystemAuditPage />
      </RoleRoute>
    )
  },

  {
    path: 'conversation',
    element: (
      <RoleRoute requiredRoles={[APP_ROLES.ADMIN, APP_ROLES.MANAGER, APP_ROLES.AGENT]}>
        <Conversation />
      </RoleRoute>
    )
  },
  { path: '*', element: <NotFoundPage /> } // Catch-all for paths under DashboardLayout
    ]
  },
  { path: '*', element: <Navigate to="/" replace /> } // General catch-all for any other path
]);

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}