import React from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
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
      <div className="mx-auto mt-10 max-w-md rounded-xl border bg-card p-8 text-center" role="alert">
        <span className="mx-auto mb-3 flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <FiShieldOff className="size-6" aria-hidden />
        </span>
        <h1 className="text-lg font-semibold">You don't have access to this page</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ask an administrator to change your access level if you need it.</p>
        <Button asChild variant="outline" size="sm" className="mt-4"><Link to="/dashboard">Back to dashboard</Link></Button>
      </div>
    );
  }

  return children;
}
