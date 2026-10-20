import apiClient from "./apiClient";

// ============================================================
// GET ALL ROLES
// ============================================================

export const getRoles = async () => {
  const response = await apiClient.get("/roles/");

  return response.data;
};

// ============================================================
// GET SINGLE ROLE
// ============================================================

export const getRole = async (roleId) => {
  const response = await apiClient.get(
    `/roles/${roleId}/`
  );

  return response.data;
};

// ============================================================
// CREATE ROLE
// ============================================================

export const createRole = async (roleData) => {
  const response = await apiClient.post(
    "/roles/",
    roleData
  );

  return response.data;
};

// ============================================================
// UPDATE ROLE
// ============================================================

export const updateRole = async (roleId, roleData) => {
  const response = await apiClient.patch(
    `/roles/${roleId}/`,
    roleData
  );

  return response.data;
};

// ============================================================
// DELETE ROLE
// ============================================================

export const deleteRole = async (roleId) => {
  const response = await apiClient.delete(
    `/roles/${roleId}/`
  );

  return response.data;
};

// ============================================================
// GET ROLE PERMISSIONS
// ============================================================

export const getRolePermissions = async (roleId) => {
  const response = await apiClient.get(
    `/roles/${roleId}/permissions/`
  );

  return response.data;
};

// ============================================================
// ASSIGN ROLE PERMISSION
// ============================================================

export const assignRolePermission = async (
  roleId,
  permissionId
) => {
  const response = await apiClient.post(
    `/roles/${roleId}/permissions/`,
    {
      permission_id: permissionId,
    }
  );

  return response.data;
};

// ============================================================
// REMOVE ROLE PERMISSION
// ============================================================

export const removeRolePermission = async (
  roleId,
  permissionId
) => {
  const response = await apiClient.delete(
    `/roles/${roleId}/permissions/${permissionId}/`
  );

  return response.data;
};

// ============================================================
// GET ALL PERMISSIONS
// ============================================================

export const getPermissions = async () => {
  const response = await apiClient.get(
    "/permissions/"
  );

  return response.data;
};

// ============================================================
// UPDATE ROLE PERMISSIONS
// ============================================================

export const updateRolePermissions = async (
  roleId,
  permissionIds
) => {
  const response = await apiClient.put(
    `/roles/${roleId}/permissions/`,
    {
      permission_ids: permissionIds,
    }
  );

  return response.data;
};