
import { useState } from "react";
import { useAuth } from "./auth/AuthContext";
import "./App.css";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Roles from "./pages/Roles";
import AuditLogs from "./pages/AuditLogs";

import ProtectedRoute from "./auth/ProtectedRoute";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Sign in failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo">S</div>
          <h1>Sentra</h1>
        </div>

        <div className="login-heading">
          <h2>Sign in</h2>
          <p>User &amp; access management console</p>
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          <div className="login-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email"
              autoComplete="username"
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="login-footer">
          <p className="login-demo">
            Demo: any email + password
          </p>

          <button
            type="button"
            className="login-create-account"
            onClick={() =>
              alert("Account creation will be added later.")
            }
          >
            Create account
          </button>
        </div>
      </div>
    </div>
  );
}

function PermissionRoute({ permission, children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="dashboard-message">
        Loading SENTRA...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  const permissions = Array.isArray(user.permissions)
    ? user.permissions
    : [];

  if (!permissions.includes(permission)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/roles" element={<Roles />} />

          <Route
            path="/audit-logs"
            element={
              <PermissionRoute permission="audit.view">
                <AuditLogs />
              </PermissionRoute>
            }
          />
        </Route>

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;