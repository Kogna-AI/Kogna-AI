import { BackendUser } from "./UserContext";
import { AuthUser } from "./UserContext";
/**
 * Check if user has a specific permission
 */
function isBackendUser(user: any): user is BackendUser {
  return !!user && "rbac" in user;
}

export function hasPermission(
  user: AuthUser | null,
  permission: string
): boolean {
  if (!isBackendUser(user)) return false;

  return user.rbac.permissions.includes(permission);
}
