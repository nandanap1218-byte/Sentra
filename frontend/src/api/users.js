
import apiClient from "./apiClient";

// ============================================================
// GET USERS
// ============================================================

export const getUsers = async ({
  search = "",
  role = "",
  isActive = "",
  ordering = "-created_at",
  page = 1,
  pageSize = 4,
} = {}) => {
  const params = {
    page,
    page_size: pageSize,
    ordering,
  };

  if (search.trim()) {
    params.search = search.trim();
  }

  if (role) {
    params.role = role;
  }

  if (isActive !== "") {
    params.is_active = isActive;
  }

  const response = await apiClient.get("/users/", {
    params,
  });

  return response.data;
};

// ============================================================
// GET SINGLE USER
// ============================================================

export const getUser = async (userId) => {
  const response = await apiClient.get(
    `/users/${userId}/`
  );

  return response.data;
};

// ============================================================
// CREATE USER
// Includes temporary error logging for debugging
// ============================================================

export const createUser = async (userData) => {
  try {
    const response = await apiClient.post(
      "/users/",
      userData
    );

    return response.data;
  } catch (error) {
    console.error(
      "Create user status:",
      error.response?.status
    );

    console.error(
  "Create user response:",
  JSON.stringify(error.response?.data, null, 2)
);
    console.error(
      "Create user submitted fields:",
      Object.keys(userData)
    );

    throw error;
  }
};

// ============================================================
// UPDATE USER
// ============================================================

export const updateUser = async (userId, userData) => {
  const response = await apiClient.patch(
    `/users/${userId}/`,
    userData
  );

  return response.data;
};

// ============================================================
// DELETE / DEACTIVATE USER
// ============================================================

export const deleteUser = async (userId) => {
  const response = await apiClient.delete(
    `/users/${userId}/`
  );

  return response.data;
};

// ============================================================
// GET USER ROLES
// ============================================================

export const getUserRoles = async (userId) => {
  const response = await apiClient.get(
    `/users/${userId}/roles/`
  );

  return response.data;
};

// ============================================================
// ASSIGN SINGLE USER ROLE
// ============================================================

export const assignUserRole = async (
  userId,
  roleId
) => {
  const response = await apiClient.post(
    `/users/${userId}/roles/`,
    {
      role_id: roleId,
    }
  );

  return response.data;
};

// ============================================================
// REMOVE SINGLE USER ROLE
// ============================================================

export const removeUserRole = async (
  userId,
  roleId
) => {
  const response = await apiClient.delete(
    `/users/${userId}/roles/${roleId}/`
  );

  return response.data;
};

// ============================================================
// UPDATE COMPLETE USER ROLE SET
// ============================================================

export const updateUserRoles = async (
  userId,
  roleIds
) => {
  const response = await apiClient.put(
    `/users/${userId}/roles/`,
    {
      role_ids: roleIds,
    }
  );

  return response.data;
};

// ============================================================
// EXPORT USERS TO EXCEL
// ============================================================

export const exportUsers = async ({
  search = "",
  role = "",
  isActive = "",
  ordering = "-created_at",
} = {}) => {
  const params = {
    ordering,
  };

  if (search.trim()) {
    params.search = search.trim();
  }

  if (role) {
    params.role = role;
  }

  if (isActive !== "") {
    params.is_active = isActive;
  }

  const response = await apiClient.get(
    "/users/export/",
    {
      params,
      responseType: "blob",
    }
  );

  return response.data;
};
