import { createContext, useContext, useEffect, useState } from "react";

import {
  loginUser,
  logoutUser,
  refreshAccessToken,
} from "../api/auth";

import { getCurrentUser } from "../api/me";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore the session when the application starts.
  useEffect(() => {
    const restoreSession = async () => {
      try {
        await refreshAccessToken();

        const currentUser = await getCurrentUser();

        setUser(currentUser);
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (email, password) => {
    const response = await loginUser(email, password);

    const currentUser = await getCurrentUser();

    setUser(currentUser);

    return response;
  };

  const logout = async () => {
    try {
      await logoutUser();
    } finally {
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}