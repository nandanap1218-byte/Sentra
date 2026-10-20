
import apiClient from "./apiClient";

const getArray = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
};

const getTotalCount = (data) => {
  if (typeof data?.count === "number") {
    return data.count;
  }

  return getArray(data).length;
};

export const getDashboardData = async () => {
  const [
    meResponse,
    usersResponse,
    rolesResponse,
    permissionsResponse,
    auditResponse,
  ] = await Promise.allSettled([
    apiClient.get("/me/"),
    apiClient.get("/users/"),
    apiClient.get("/roles/"),
    apiClient.get("/permissions/"),
    apiClient.get("/audit-logs/"),
  ]);

  const currentUser =
    meResponse.status === "fulfilled"
      ? meResponse.value.data
      : null;

  const usersData =
    usersResponse.status === "fulfilled"
      ? usersResponse.value.data
      : [];

  const rolesData =
    rolesResponse.status === "fulfilled"
      ? rolesResponse.value.data
      : [];

  const permissionsData =
    permissionsResponse.status === "fulfilled"
      ? permissionsResponse.value.data
      : [];

  const auditData =
    auditResponse.status === "fulfilled"
      ? auditResponse.value.data
      : [];

  const users = getArray(usersData);
  const roles = getArray(rolesData);
  const permissions = getArray(permissionsData);
  const auditLogs = getArray(auditData);

  const assignedPermissions = Array.isArray(
    currentUser?.permissions
  )
    ? currentUser.permissions
    : [];

  const userRoles = Array.isArray(currentUser?.roles)
    ? currentUser.roles
    : [];

  const roleName = userRoles
    .map((role) => role.name)
    .filter(Boolean)
    .join(", ");

  return {
    currentUser,
    roleName,
    assignedPermissions,
    users,
    roles,
    permissions,
    auditLogs,

    counts: {
      users: getTotalCount(usersData),

      activeUsers:
        typeof usersData?.active_count === "number"
          ? usersData.active_count
          : users.filter(
              (user) => user.is_active === true
            ).length,

      roles: getTotalCount(rolesData),

      permissions: assignedPermissions.length,

      auditEvents: getTotalCount(auditData),
    },
  };
};
