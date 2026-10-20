
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { logoutUser } from "../api/auth";
import apiClient from "../api/apiClient";
import "./Sidebar.css";

const navItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: (
      <svg viewBox="0 0 24 24">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    label: "Users",
    path: "/users",
    icon: (
      <svg viewBox="0 0 24 24">
        <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="10" cy="7" r="4" />
        <path d="M20 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    label: "Roles & Permissions",
    path: "/roles",
    icon: (
      <svg viewBox="0 0 24 24">
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    ),
  },
  {
    label: "Audit Log",
    path: "/audit-logs",
    permission: "audit.view",
    icon: (
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </svg>
    ),
  },
];

function Sidebar() {
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function loadCurrentUser() {
      try {
        const response = await apiClient.get("/me/");

        if (mounted) {
          setCurrentUser(response.data);
        }
      } catch (error) {
        console.error("Unable to load sidebar user:", error);
      }
    }

    loadCurrentUser();

    return () => {
      mounted = false;
    };
  }, []);

  const fullName = currentUser?.full_name?.trim() || "User";

  const roleName = Array.isArray(currentUser?.roles)
    ? currentUser.roles
        .map((role) => role.name)
        .filter(Boolean)
        .join(", ") || "User"
    : "User";

  const permissions = Array.isArray(currentUser?.permissions)
    ? currentUser.permissions
    : [];

  const visibleNavItems = navItems.filter(
    (item) =>
      !item.permission || permissions.includes(item.permission)
  );

  const initials =
    fullName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0].toUpperCase())
      .join("") || "U";

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      navigate("/");
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">S</div>
        <h2>Sentra</h2>
      </div>

      <nav className="sidebar-nav">
        {visibleNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/dashboard"}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " active" : ""}`
            }
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-profile">
          <div className="sidebar-avatar">{initials}</div>

          <div className="sidebar-profile-info">
            <strong>{fullName}</strong>
            <span>{roleName}</span>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
            title="Logout"
            aria-label="Logout"
          >
            <svg viewBox="0 0 24 24">
              <path d="M10 17l5-5-5-5" />
              <path d="M15 12H3" />
              <path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
