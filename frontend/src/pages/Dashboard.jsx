
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getDashboardData } from "../api/dashboard";
import "./Dashboard.css";

function Dashboard() {
  const [stats, setStats] = useState({
    users: 0,
    activeUsers: 0,
    roles: 0,
    auditEvents: 0,
    permissions: 0,
  });

  const [roleName, setRoleName] = useState("User");
  const [assignedPermissions, setAssignedPermissions] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const canViewAuditLogs =
    assignedPermissions.includes("audit.view");

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const data = await getDashboardData();

        if (!mounted) return;

        const permissions = Array.isArray(
          data.assignedPermissions
        )
          ? data.assignedPermissions
          : [];

        setRoleName(data.roleName || "User");
        setAssignedPermissions(permissions);

        const users = Array.isArray(data.users)
          ? data.users
          : [];

        const roles = Array.isArray(data.roles)
          ? data.roles
          : [];

        // Only use audit data when the current user has permission.
        const auditLogs = permissions.includes("audit.view") &&
          Array.isArray(data.auditLogs)
          ? data.auditLogs
          : [];

        const counts = data.counts || {};

        setStats({
          users:
            typeof counts.users === "number"
              ? counts.users
              : users.length,

          activeUsers:
            typeof counts.activeUsers === "number"
              ? counts.activeUsers
              : users.filter(
                  (user) =>
                    user.is_active === true ||
                    user.is_active === 1 ||
                    user.is_active === "true"
                ).length,

          roles:
            typeof counts.roles === "number"
              ? counts.roles
              : roles.length,

          auditEvents: permissions.includes("audit.view")
            ? typeof counts.auditEvents === "number"
              ? counts.auditEvents
              : auditLogs.length
            : 0,

          permissions: permissions.length,
        });

        // Sort newest first and display only four activities.
        const sortedLogs = [...auditLogs].sort((a, b) => {
          const dateA = new Date(
            a.timestamp || a.created_at || a.createdAt || 0
          ).getTime();

          const dateB = new Date(
            b.timestamp || b.created_at || b.createdAt || 0
          ).getTime();

          return dateB - dateA;
        });

        setRecentActivity(sortedLogs.slice(0, 4));
      } catch (err) {
        if (mounted) {
          setError(
            err.response?.data?.detail ||
              err.message ||
              "Unable to load dashboard data."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  function getAction(log) {
    return String(
      log.action ||
        log.event_type ||
        log.event ||
        "Activity"
    );
  }

  function getActionClass(action) {
    const value = action.toLowerCase().trim();

    if (
      value.includes("login") ||
      value.includes("logout") ||
      value.startsWith("auth.")
    ) {
      return "activity-auth";
    }

    if (
      value.includes("user.create") ||
      value.includes("users.create") ||
      value.includes("user.register") ||
      value.includes("user_created")
    ) {
      return "activity-user-create";
    }

    if (
      value.includes("user.delete") ||
      value.includes("users.delete") ||
      value.includes("user_deleted")
    ) {
      return "activity-user-delete";
    }

    if (
      value.includes("user.update") ||
      value.includes("users.update") ||
      value.includes("user.edit") ||
      value.includes("user_updated")
    ) {
      return "activity-user-update";
    }

    if (
      value.startsWith("user.") ||
      value.startsWith("users.")
    ) {
      return "activity-user";
    }

    if (
      value.startsWith("role.") ||
      value.startsWith("roles.")
    ) {
      return "activity-role";
    }

    if (
      value.startsWith("permission.") ||
      value.startsWith("permissions.")
    ) {
      return "activity-permission";
    }

    return "activity-default";
  }

  function formatDate(log) {
    const value =
      log.timestamp ||
      log.created_at ||
      log.createdAt;

    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    const datePart = date.toLocaleDateString("en-CA", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });

    const timePart = date.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });

    return `${datePart} ${timePart}`;
  }

  function getDetail(log) {
    let metadata = log.metadata;

    if (typeof metadata === "string") {
      try {
        metadata = JSON.parse(metadata);
      } catch {
        metadata = {};
      }
    }

    metadata =
      metadata && typeof metadata === "object"
        ? metadata
        : {};

    const detail =
      metadata.detail ||
      metadata.description ||
      metadata.message ||
      log.detail ||
      log.description;

    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    const action = getAction(log).toLowerCase();

    const role =
      metadata.role_name ||
      metadata.roleName ||
      metadata.role;

    const userName =
      metadata.full_name ||
      metadata.user_name ||
      metadata.userName ||
      metadata.target_user ||
      metadata.email ||
      metadata.user_email;

    if (action.includes("role.permissions.update")) {
      return role
        ? `Updated permissions for ${role}`
        : "Role permissions updated";
    }

    if (action.includes("role.update")) {
      return role
        ? `Updated role ${role}`
        : "Role updated";
    }

    if (action.includes("role.create")) {
      return role
        ? `Created role ${role}`
        : "New role created";
    }

    if (action.includes("role.delete")) {
      return role
        ? `Deleted role ${role}`
        : "Role deleted";
    }

    if (action.includes("user.roles.update")) {
      return userName
        ? `Updated roles for ${userName}`
        : "User roles updated";
    }

    if (action.includes("user.update")) {
      return userName
        ? `Updated ${userName}`
        : "User updated";
    }

    if (action.includes("user.create")) {
      return userName
        ? `Created ${userName}`
        : "New user created";
    }

    if (action.includes("user.register")) {
      return userName
        ? `Registered ${userName}`
        : "New user registered";
    }

    if (action.includes("login")) {
      return userName
        ? `${userName} signed in`
        : "Signed in";
    }

    if (action.includes("logout")) {
      return userName
        ? `${userName} signed out`
        : "Signed out";
    }

    if (action.includes("delete")) {
      return userName
        ? `Deleted ${userName}`
        : "Record deleted";
    }

    if (action.includes("create")) {
      return userName
        ? `Created ${userName}`
        : "New record created";
    }

    if (action.includes("permission.assign")) {
      return "Permission assigned to role";
    }

    if (action.includes("permission.remove")) {
      return "Permission removed from role";
    }

    return "Activity recorded";
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-content sentra-dashboard">
        <header className="dashboard-page-header">
          <div>
            <h1>Dashboard</h1>
            <p>
              Signed in as {roleName} — {stats.permissions} of 8
              permissions granted
            </p>
          </div>
        </header>

        {loading && (
          <div className="dashboard-message">
            Loading dashboard...
          </div>
        )}

        {error && (
          <div className="dashboard-error" role="alert">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <section className="dashboard-summary">
              <div className="dashboard-card">
                <span className="dashboard-card-label">
                  Total users
                </span>
                <strong>{stats.users}</strong>
              </div>

              <div className="dashboard-card active-kpi-card">
                <span className="dashboard-card-label">
                  Active
                </span>
                <strong className="active-kpi-value">
                  {stats.activeUsers}
                </strong>
              </div>

              <div className="dashboard-card">
                <span className="dashboard-card-label">
                  Roles
                </span>
                <strong>{stats.roles}</strong>
              </div>

              {canViewAuditLogs && (
                <div className="dashboard-card">
                  <span className="dashboard-card-label">
                    Audit events
                  </span>
                  <strong>{stats.auditEvents}</strong>
                </div>
              )}
            </section>

            {canViewAuditLogs && (
              <section className="dashboard-activity dashboard-activity-expanded">
                <div className="dashboard-section-header">
                  <h2>Recent activity</h2>

                  <Link
                    className="dashboard-text-link"
                    to="/audit-logs"
                  >
                    View audit log
                    <span aria-hidden="true"> →</span>
                  </Link>
                </div>

                <div className="compact-activity-list expanded-activity-list">
                  {recentActivity.length > 0 ? (
                    recentActivity.map((log, index) => {
                      const action = getAction(log);
                      const actionClass = getActionClass(action);

                      return (
                        <div
                          className="compact-activity-row expanded-activity-row"
                          key={log.id || `${action}-${index}`}
                        >
                          <time className="compact-activity-date">
                            {formatDate(log)}
                          </time>

                          <span
                            className={`compact-activity-action ${actionClass}`}
                          >
                            {action}
                          </span>

                          <span className="compact-activity-detail">
                            {getDetail(log)}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <p className="dashboard-activity-empty">
                      No recent activity found.
                    </p>
                  )}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
