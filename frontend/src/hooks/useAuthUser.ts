import { useUser } from "@/app/components/auth/UserContext";
import { BackendUser } from "@/app/components/auth/UserContext";
import { LoginUser } from "@/services/api";
export function useAuthUser() {
  const { user, isAuthenticated, loading } = useUser();

  const isBackendUser = (u: any): u is BackendUser => {
    return u && typeof u === "object" && "rbac" in u;
  };

  const firstName = user?.first_name ?? "";
  const lastName = user?.second_name ?? "";

  const fullName = [firstName, lastName].filter(Boolean).join(" ");

  const hasPermission = (permission: string): boolean => {
    if (!user || !isBackendUser(user)) return false;
    return user.rbac.permissions.includes(permission);
  };

  const hasRoleLevel = (minLevel: number): boolean => {
    if (!user || !isBackendUser(user)) return false;
    return user.rbac.role_level >= minLevel;
  };

  return {
    /** raw */
    user,
    isAuthenticated,
    loading,

    /** identity */
    id: user?.id ?? null,
    email: user?.email ?? null,
    organizationId: user?.organization_id ?? null,

    /** name */
    firstName,
    lastName,
    fullName,

    /** rbac */
    isBackendUser: isBackendUser(user),
    roleName: isBackendUser(user) ? user.rbac.role_name : null,
    roleLevel: isBackendUser(user) ? user.rbac.role_level : null,

    hasPermission,
    hasRoleLevel,
  };
}
