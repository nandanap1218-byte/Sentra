import apiClient, { setAccessToken, clearAccessToken } from "./apiClient";

export const loginUser = async (email, password) => {
  try {
    const response = await apiClient.post("/login/", {
      email,
      password,
    });

    const { access } = response.data;

    // Keep access token only in memory.
    setAccessToken(access);

    return response.data;
  } catch (error) {
    const message =
      error.response?.data?.detail ||
      "Login failed. Please check your email and password.";

    throw new Error(message);
  }
};

export const logoutUser = async () => {
  try {
    await apiClient.post("/logout/");
  } finally {
    clearAccessToken();
  }
};

export const refreshAccessToken = async () => {
  try {
    const response = await apiClient.post("/refresh/");

    const { access } = response.data;

    setAccessToken(access);

    return access;
  } catch (error) {
    clearAccessToken();
    throw error;
  }
};