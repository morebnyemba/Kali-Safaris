import AnalyticsPage from './pages/AnalyticsPage';
// Filename: src/App.jsx
import React from 'react';
import { RouterProvider, createBrowserRouter, Navigate, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext'; // Your AuthProvider
import ProtectedRoute from './components/ProtectedRoute'; // Your ProtectedRoute

import DashboardLayout from './components/DashboardLayout';
import Dashboard from './pages/Dashboard';
import ApiSettings from './pages/ApiSettings';
import FlowsPage from './pages/FlowsPage';
import FlowEditorPage from './pages/FlowEditorPage'; // <--- IMPORT FlowEditorPage
import MediaLibraryPage from './pages/MediaLibraryPage';
import ContactsPage from './pages/ContactsPage';
import Conversation from './pages/Conversation';
import LoginPage from './pages/LoginPage';
import RoleRoute from './components/RoleRoute';
import { APP_ROLES } from './lib/rbac';
import AdminOverviewPage from './pages/admin/AdminOverviewPage';
import UsersCrudPage from './pages/admin/UsersCrudPage';
import RolesPermissionsPage from './pages/admin/RolesPermissionsPage';
import SystemAuditPage from './pages/admin/SystemAuditPage';


import BookingsPage from './pages/BookingsPage';
import InquiriesPage from './pages/InquiriesPage';

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
      { path: 'api-settings', element: <ApiSettings /> },
      
      // Flow Management
      { path: 'flows', element: <FlowsPage /> }, // Page to list all flows
      { path: 'flows/new', element: <FlowEditorPage /> }, // <--- ADDED: Route to create a new flow
      { path: 'flows/edit/:flowId', element: <FlowEditorPage /> }, // <--- ADDED: Route to edit an existing flow
      
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