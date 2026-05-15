export const APP_ROLES = {
  ADMIN: "admin",
  MANAGER: "manager",
  AGENT: "agent",
};

function normalizeList(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((v) => v.trim()).filter(Boolean);
  return [];
}

export function getRoleFromUser(user) {
  if (!user) return APP_ROLES.AGENT;

  if (user.role && Object.values(APP_ROLES).includes(user.role)) {
    return user.role;
  }

  const groups = normalizeList(user.groups).map((g) => g.toLowerCase());
  if (user.is_superuser || groups.includes("admin") || groups.includes("administrators")) {
    return APP_ROLES.ADMIN;
  }
  if (user.is_staff || groups.includes("manager") || groups.includes("operations")) {
    return APP_ROLES.MANAGER;
  }
  return APP_ROLES.AGENT;
}

export function extractPermissions(user) {
  if (!user) return [];
  const rawPermissions = normalizeList(user.permissions);
  return rawPermissions.map((p) => String(p).toLowerCase());
}

export function hasRole(user, requiredRoles = []) {
  if (!requiredRoles || requiredRoles.length === 0) return true;
  const role = getRoleFromUser(user);
  return requiredRoles.includes(role);
}

export function hasPermission(user, requiredPermissions = []) {
  if (!requiredPermissions || requiredPermissions.length === 0) return true;
  const userPermissions = extractPermissions(user);
  return requiredPermissions.every((permission) =>
    userPermissions.includes(String(permission).toLowerCase())
  );
}

export function canAccess(user, requiredRoles = [], requiredPermissions = []) {
  return hasRole(user, requiredRoles) && hasPermission(user, requiredPermissions);
}
