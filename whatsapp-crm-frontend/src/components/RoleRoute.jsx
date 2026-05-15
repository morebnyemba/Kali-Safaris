import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { FiShieldOff } from "react-icons/fi";
import { useAuth } from "@/context/AuthContext";
import { canAccess } from "@/lib/rbac";

export default function RoleRoute({
  children,
  requiredRoles = [],
  requiredPermissions = [],
}) {
  const { user } = useAuth();
  const location = useLocation();

  const allowed = canAccess(user, requiredRoles, requiredPermissions);

  if (!allowed) {
    if (!user) {
      return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900/40 dark:bg-red-950/30">
        <FiShieldOff className="mx-auto mb-3 h-8 w-8 text-red-600 dark:text-red-400" />
        <h2 className="mb-2 text-xl font-semibold text-red-700 dark:text-red-300">Access denied</h2>
        <p className="text-sm text-red-700/90 dark:text-red-300/90">
          You do not have the required role or permission to view this admin section.
        </p>
      </div>
    );
  }

  return children;
}
