
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/auth";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Separate client for refresh requests.
// This prevents the refresh request from triggering
// the normal response interceptor again.
const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let accessToken = null;

export const setAccessToken = (token) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

export const clearAccessToken = () => {
  accessToken = null;
};

// Attach the current access token to API requests.
apiClient.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

let refreshPromise = null;

// Automatically refresh an expired access token.
apiClient.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.includes("/refresh/") ||
      originalRequest.url?.includes("/login/") ||
      originalRequest.url?.includes("/register/")
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      // If another request is already refreshing,
      // wait for the same refresh request.
      if (!refreshPromise) {
        refreshPromise = refreshClient
          .post("/refresh/")
          .then((response) => {
            const newAccessToken = response.data?.access;

            if (!newAccessToken) {
              throw new Error(
                "The refresh endpoint did not return an access token."
              );
            }

            setAccessToken(newAccessToken);
            return newAccessToken;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newAccessToken = await refreshPromise;

      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return apiClient(originalRequest);
    } catch (refreshError) {
      clearAccessToken();

      // Only redirect if the user has left the login page.
      if (window.location.pathname !== "/") {
        window.location.replace("/");
      }

      return Promise.reject(refreshError);
    }
  }
);

export default apiClient;