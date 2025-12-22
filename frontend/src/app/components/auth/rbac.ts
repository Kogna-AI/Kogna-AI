import { BackendUser } from "./UserContext";
/**
 * Check if user has a specific permission
 */
function isBackendUser(user: any): user is BackendUser {
  return !!user && "rbac" in user;
}

export function hasPermission(
  user: BackendUser | null,
  permission: string
): boolean {
  if (!isBackendUser(user)) return false;

  return user.rbac.permissions.includes(permission);
}
