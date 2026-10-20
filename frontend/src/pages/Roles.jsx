
import { useEffect, useMemo, useState } from "react";
import Sidebar from "../components/Sidebar";
import {
  getRoles,
  createRole,
  updateRole,
  deleteRole,
  getRolePermissions,
  updateRolePermissions,
  getPermissions,
} from "../api/roles";

const GROUPS = {
  USERS: "Users",
  ROLES: "Roles",
  AUDIT: "Audit",
};

const HIDDEN_PERMISSIONS = new Set(["users.roles.assign"]);

const PERMISSION_DETAILS = {
  "users.view": {
    group: "USERS",
    description: "See the user list",
  },
  "users.create": {
    group: "USERS",
    description: "Invite / add users",
  },
  "users.edit": {
    group: "USERS",
    description: "Edit users",
  },
  "users.delete": {
    group: "USERS",
    description: "Deactivate users",
  },
  "roles.view": {
    group: "ROLES",
    description: "See roles",
  },
  "roles.manage": {
    group: "ROLES",
    description: "Create/edit roles & permissions",
  },
  "permissions.view": {
    group: "ROLES",
    description: "See permission catalogue",
  },
  "audit.view": {
    group: "AUDIT",
    description: "Read the audit log",
  },
};

const normalize = (value) =>
  String(value ?? "").trim().toLowerCase();

const getId = (item) => item?.id ?? item?.uuid ?? item?.pk;

const getPermissionCode = (permission) => {
  if (typeof permission === "string") {
    return permission.trim();
  }

  if (!permission || typeof permission !== "object") {
    return "";
  }

  return String(
    permission.permission_name ??
      permission.codename ??
      permission.code ??
      permission.permission_code ??
      permission.slug ??
      permission.name ??
      permission.permission?.codename ??
      permission.permission?.code ??
      ""
  ).trim();
};

const unwrapList = (response) => {
  const data = response?.data ?? response;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data?.roles)) return data.roles;
  if (Array.isArray(data?.permissions)) return data.permissions;
  if (Array.isArray(data?.role_permissions)) {
    return data.role_permissions;
  }

  return [];
};

function sortRoles(rolesList) {
  const priority = {
    admin: 1,
    manager: 2,
    viewer: 3,
    "new role": 4,
  };

  return [...rolesList].sort((a, b) => {
    const nameA = normalize(a.name || a.role_name);
    const nameB = normalize(b.name || b.role_name);

    return (priority[nameA] ?? 5) - (priority[nameB] ?? 5);
  });
}

const getErrorMessage = (err, fallback) => {
  const data = err?.response?.data;

  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.error === "string") return data.error;
  if (typeof data === "string") return data;

  if (data && typeof data === "object") {
    return (
      Object.entries(data)
        .map(([key, value]) => {
          const message = Array.isArray(value)
            ? value.join(", ")
            : typeof value === "string"
              ? value
              : JSON.stringify(value);

          return `${key}: ${message}`;
        })
        .join(" | ") || fallback
    );
  }

  return fallback;
};

function Roles() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingRolePermissions, setLoadingRolePermissions] =
    useState(false);
  const [savingPermissions, setSavingPermissions] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState(null);
  const [roleName, setRoleName] = useState("");
  const [roleDescription, setRoleDescription] = useState("");
  const [savingRole, setSavingRole] = useState(false);

  async function loadRolePermissions(role) {
    if (!role) {
      setSelectedPermissions([]);
      return;
    }

    setLoadingRolePermissions(true);

    try {
      const response = await getRolePermissions(getId(role));
      const list = response?.permissions
        ? response.permissions
        : unwrapList(response);

      const codes = list
        .map(getPermissionCode)
        .filter(Boolean)
        .filter((code) => !HIDDEN_PERMISSIONS.has(code));

      setSelectedPermissions([...new Set(codes)]);
    } catch (err) {
      setSelectedPermissions([]);
      setError(
        getErrorMessage(
          err,
          "Could not load permissions for this role."
        )
      );
    } finally {
      setLoadingRolePermissions(false);
    }
  }

  async function loadData(preferredId = null) {
    setLoading(true);
    setError("");

    try {
      const [roleResponse, permissionResponse] = await Promise.all([
        getRoles(),
        getPermissions(),
      ]);

      const roleList = sortRoles(unwrapList(roleResponse));

      // Hide users.roles.assign from the permission catalogue.
      const permissionList = unwrapList(permissionResponse).filter(
        (permission) =>
          !HIDDEN_PERMISSIONS.has(getPermissionCode(permission))
      );

      setRoles(roleList);
      setPermissions(permissionList);

      const nextSelected =
        roleList.find(
          (role) =>
            preferredId != null &&
            String(getId(role)) === String(preferredId)
        ) ||
        roleList.find(
          (role) =>
            normalize(role.name || role.role_name) === "manager"
        ) ||
        roleList[0] ||
        null;

      setSelectedRole(nextSelected);

      if (nextSelected) {
        await loadRolePermissions(nextSelected);
      } else {
        setSelectedPermissions([]);
      }
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Could not load roles and permissions."
        )
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const selectedRoleName =
    selectedRole?.name || selectedRole?.role_name || "Role";

  const isSystemRole = ["admin", "manager", "viewer"].includes(
    normalize(selectedRoleName)
  );

  const permissionItems = useMemo(() => {
    const byCode = new Map();

    permissions.forEach((permission) => {
      const code = getPermissionCode(permission);

      if (code && !HIDDEN_PERMISSIONS.has(code)) {
        byCode.set(code, permission);
      }
    });

    Object.keys(PERMISSION_DETAILS).forEach((code) => {
      if (!byCode.has(code)) {
        byCode.set(code, { code, name: code });
      }
    });

    return [...byCode.entries()].map(([code, permission]) => ({
      code,
      id: getId(permission),
      description:
        PERMISSION_DETAILS[code]?.description ||
        permission?.description ||
        permission?.details ||
        "Permission access",
      group:
        PERMISSION_DETAILS[code]?.group ||
        (code.startsWith("audit.")
          ? "AUDIT"
          : code.startsWith("roles.") ||
              code.startsWith("permissions.")
            ? "ROLES"
            : "USERS"),
    }));
  }, [permissions]);

  async function chooseRole(role) {
    setSelectedRole(role);
    setSelectedPermissions([]);
    setError("");
    setNotice("");

    await loadRolePermissions(role);
  }

  async function openCreate() {
    if (savingRole) return;

    setError("");
    setNotice("");
    setSavingRole(true);

    try {
      const response = await createRole({
        name: "New role",
        description: "Describe this role",
      });

      const created = response?.data ?? response;
      const refreshedResponse = await getRoles();
      const refreshedRoles = unwrapList(refreshedResponse);
      const createdId = getId(created);

      const newRole =
        refreshedRoles.find(
          (role) =>
            createdId != null &&
            String(getId(role)) === String(createdId)
        ) ||
        refreshedRoles.find(
          (role) =>
            normalize(role.name || role.role_name) === "new role" &&
            normalize(role.description) === "describe this role"
        );

      if (!newRole) {
        await loadData();
        setNotice(
          "The role was created. Refresh the role list if needed."
        );
        return;
      }

      setRoles(sortRoles(refreshedRoles));
      setSelectedRole(newRole);
      setSelectedPermissions([]);
      setNotice("New role created successfully.");
    } catch (err) {
      setError(
        getErrorMessage(err, "Could not create the new role.")
      );
    } finally {
      setSavingRole(false);
    }
  }

  function openEdit() {
    if (!selectedRole || isSystemRole) return;

    setRoleName(selectedRole.name || selectedRole.role_name || "");
    setRoleDescription(selectedRole.description || "");
    setModal({ mode: "edit" });
    setError("");
    setNotice("");
  }

  async function submitRole(event) {
    event.preventDefault();

    if (!selectedRole || isSystemRole) return;

    if (!roleName.trim()) {
      setError("Enter a role name.");
      return;
    }

    setSavingRole(true);
    setError("");
    setNotice("");

    try {
      await updateRole(getId(selectedRole), {
        name: roleName.trim(),
        description: roleDescription.trim(),
      });

      const selectedId = getId(selectedRole);
      setModal(null);
      setNotice("Role updated successfully.");

      await loadData(selectedId);
    } catch (err) {
      setError(
        getErrorMessage(err, "Could not update this role.")
      );
    } finally {
      setSavingRole(false);
    }
  }

  async function removeRole() {
    if (!selectedRole || isSystemRole) return;

    if (!window.confirm(`Delete the role "${selectedRoleName}"?`)) {
      return;
    }

    setError("");
    setNotice("");

    try {
      await deleteRole(getId(selectedRole));

      setSelectedRole(null);
      setSelectedPermissions([]);
      setNotice("Role deleted successfully.");

      await loadData();
    } catch (err) {
      setError(
        getErrorMessage(err, "Could not delete this role.")
      );
    }
  }

  function togglePermission(code) {
    if (
      !selectedRole ||
      HIDDEN_PERMISSIONS.has(code) ||
      loadingRolePermissions ||
      savingPermissions
    ) {
      return;
    }

    const nextPermissions = selectedPermissions.includes(code)
      ? selectedPermissions.filter((item) => item !== code)
      : [...selectedPermissions, code];

    setSelectedPermissions(nextPermissions);
    void savePermissions(nextPermissions);
  }

  async function savePermissions(permissionCodes) {
    if (!selectedRole || savingPermissions || loadingRolePermissions) {
      return;
    }

    setSavingPermissions(true);
    setError("");
    setNotice("");

    try {
      // Save only visible permission UUIDs. The hidden permission is
      // not modified by this screen's permission selections.
      const permissionIds = permissions
        .filter((permission) =>
          permissionCodes.includes(getPermissionCode(permission))
        )
        .map(getId)
        .filter(Boolean);

      // Preserve users.roles.assign if it is already assigned.
      // This keeps hiding it from the UI from silently revoking it.
      const currentResponse = await getRolePermissions(
        getId(selectedRole)
      );
      const currentList = currentResponse?.permissions
        ? currentResponse.permissions
        : unwrapList(currentResponse);

      const hiddenPermissionIds = currentList
        .filter((permission) =>
          HIDDEN_PERMISSIONS.has(getPermissionCode(permission))
        )
        .map((permission) => {
          if (typeof permission === "string") return null;

          return (
            permission.permission ??
            permission.permission_id ??
            permission.id ??
            permission.uuid ??
            null
          );
        })
        .filter(Boolean);

      await updateRolePermissions(
        getId(selectedRole),
        [...new Set([...permissionIds, ...hiddenPermissionIds])]
      );

      await loadRolePermissions(selectedRole);
      setNotice("Permissions saved successfully.");
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Could not save permissions. Check the role-permissions API endpoint."
        )
      );

      await loadRolePermissions(selectedRole);
    } finally {
      setSavingPermissions(false);
    }
  }

  function userCount(role) {
    return (
      role?.user_count ??
      role?.users_count ??
      role?.users?.length ??
      role?.assigned_users_count ??
      0
    );
  }

  return (
    <div className="dashboard-layout roles-reference-layout">
      <Sidebar />

      <main className="dashboard-content roles-reference-content">
        <style>{`
          .roles-reference-layout {
            min-height: 100vh;
            background: #f5f7fa;
            color: #111827;
          }
          .roles-reference-content {
            padding: 30px 40px 48px;
            min-width: 0;
            flex: 1;
          }
          .roles-reference-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin: 0 0 24px;
          }
          .roles-reference-header h1 {
            font-size: 26px;
            line-height: 1.25;
            font-weight: 700;
            margin: 0 0 5px;
            color: #101827;
            letter-spacing: -.35px;
          }
          .roles-reference-subtitle {
            margin: 0;
            color: #64748b;
            font-size: 14px;
          }
          .roles-reference-primary {
            background: #0e7c75;
            border: 1px solid #0e7c75;
            color: white;
            border-radius: 11px;
            padding: 12px 19px;
            font-weight: 700;
            font-size: 14px;
            min-height: 46px;
            cursor: pointer;
            white-space: nowrap;
          }
          .roles-reference-primary:hover { background: #0b6b65; }
          .roles-reference-primary:disabled {
            opacity: .6;
            cursor: wait;
          }
          .roles-reference-body {
            display: grid;
            grid-template-columns: 300px minmax(0, 1fr);
            gap: 20px;
            align-items: start;
          }
          .roles-reference-list,
          .roles-reference-detail {
            background: #fff;
            border: 1px solid #dfe5ed;
            border-radius: 12px;
            overflow: hidden;
          }
          .roles-reference-role {
            width: 100%;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            text-align: left;
            padding: 18px 20px 16px;
            background: #fff;
            border: 0;
            border-bottom: 1px solid #edf0f4;
            cursor: pointer;
            color: #111827;
            min-height: 74px;
          }
          .roles-reference-role:last-child { border-bottom: 0; }
          .roles-reference-role.active {
            background: #f3faf9;
            border-left: 3px solid #0e8179;
            padding-left: 17px;
          }
          .roles-reference-role-name {
            font-size: 16px;
            font-weight: 700;
            margin: 0 0 5px;
            line-height: 1.2;
          }
          .roles-reference-role-description {
            font-size: 13px;
            color: #8290a6;
            margin: 0;
            line-height: 1.35;
          }
          .roles-reference-count {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            color: #8190a6;
            font-size: 12px;
            white-space: nowrap;
            padding-top: 4px;
          }
          .roles-reference-detail {
            padding: 25px 30px 43px;
            min-height: 540px;
          }
          .roles-reference-detail-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 23px;
          }
          .roles-reference-detail-head h2 {
            font-size: 23px;
            line-height: 1.3;
            margin: 0 0 5px;
            font-weight: 700;
            color: #111827;
          }
          .roles-reference-detail-head p {
            margin: 0;
            color: #64748b;
            font-size: 14px;
          }
          .roles-reference-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
          }
          .roles-reference-secondary {
            border: 1px solid #d8e0e9;
            background: white;
            color: #233247;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
          }
          .roles-reference-secondary:disabled {
            opacity: .45;
            cursor: not-allowed;
          }
          .roles-reference-group { margin-top: 21px; }
          .roles-reference-group-title {
            font-size: 12px;
            letter-spacing: 1px;
            font-weight: 700;
            color: #8190a6;
            margin: 0 0 10px;
            text-transform: uppercase;
          }
          .roles-reference-permission-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 9px;
          }
          .roles-reference-permission {
            font-family: inherit;
            appearance: none;
            -webkit-appearance: none;
          }
          .roles-reference-permission:disabled {
            opacity: 1;
            cursor: default;
          }
          .roles-reference-permission:focus-visible {
            outline: 3px solid rgba(14, 129, 121, .25);
            outline-offset: 2px;
          }
          .roles-reference-code {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 14px;
            font-weight: 700;
            line-height: 1.3;
            margin: 0 0 4px;
            color: #000;
            overflow-wrap: anywhere;
          }
          .roles-reference-description {
            font-size: 12px;
            color: #8290a6;
            line-height: 1.4;
            margin: 0;
            overflow-wrap: anywhere;
          }
          .roles-reference-notice,
          .roles-reference-error {
            font-size: 13px;
            border-radius: 8px;
            padding: 10px 12px;
            margin: 0 0 16px;
          }
          .roles-reference-notice {
            color: #08766e;
            background: #eaf7f5;
          }
          .roles-reference-error {
            color: #b42318;
            background: #fff0ef;
            overflow-wrap: anywhere;
          }
          .roles-reference-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-top: 24px;
            padding-top: 18px;
            border-top: 1px solid #edf0f4;
          }
          .roles-reference-footer-note {
            color: #8290a6;
            font-size: 12px;
          }
          .roles-reference-save {
            background: #0e7c75;
            color: white;
            border: 1px solid #0e7c75;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: 700;
            cursor: pointer;
          }
          .roles-reference-save:disabled {
            opacity: .55;
            cursor: not-allowed;
          }
          .roles-reference-modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, .4);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            z-index: 1000;
          }
          .roles-reference-modal {
            background: #fff;
            border-radius: 14px;
            border: 1px solid #e1e6ed;
            padding: 25px;
            width: min(440px, 100%);
            box-shadow: 0 20px 60px rgba(15, 23, 42, .18);
          }
          .roles-reference-modal h2 {
            font-size: 21px;
            margin: 0 0 18px;
          }
          .roles-reference-field {
            display: block;
            margin-bottom: 15px;
            font-size: 13px;
            font-weight: 600;
            color: #344256;
          }
          .roles-reference-field input,
          .roles-reference-field textarea {
            display: block;
            width: 100%;
            box-sizing: border-box;
            margin-top: 7px;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 11px 12px;
            font: inherit;
            font-weight: 400;
            color: #111827;
            outline: none;
          }
          .roles-reference-field input:focus,
          .roles-reference-field textarea:focus {
            border-color: #0e8179;
            box-shadow: 0 0 0 3px rgba(14, 129, 121, .1);
          }
          .roles-reference-modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 9px;
            margin-top: 22px;
          }
          @media (max-width: 1050px) {
            .roles-reference-content { padding: 25px; }
            .roles-reference-body {
              grid-template-columns: 260px minmax(0, 1fr);
            }
            .roles-reference-detail { padding: 24px; }
          }
          @media (max-width: 760px) {
            .roles-reference-content { padding: 20px 15px; }
            .roles-reference-header { align-items: flex-start; }
            .roles-reference-header h1 { font-size: 23px; }
            .roles-reference-body { grid-template-columns: 1fr; }
            .roles-reference-detail {
              min-height: 0;
              padding: 20px;
            }
            .roles-reference-permission-grid { grid-template-columns: 1fr; }
            .roles-reference-detail-head { flex-direction: column; }
          }
        `}</style>

        <header className="roles-reference-header">
          <div>
            <h1>Roles &amp; Permissions</h1>
            <p className="roles-reference-subtitle">
              Changes apply immediately and are written to the audit log
            </p>
          </div>

          <button
            className="roles-reference-primary"
            onClick={openCreate}
            disabled={savingRole}
          >
            {savingRole ? "Creating…" : "+ New role"}
          </button>
        </header>

        {notice && (
          <div className="roles-reference-notice" role="status">
            {notice}
          </div>
        )}

        {error && (
          <div className="roles-reference-error" role="alert">
            {error}
          </div>
        )}

        <section className="roles-reference-body">
          <aside className="roles-reference-list" aria-label="Roles">
            {loading ? (
              <div style={{ padding: 22, color: "#8290a6" }}>
                Loading roles…
              </div>
            ) : roles.length === 0 ? (
              <div style={{ padding: 22, color: "#8290a6" }}>
                No roles available.
              </div>
            ) : (
              roles.map((role) => {
                const name = role.name || role.role_name || "Unnamed role";
                const active =
                  String(getId(role)) === String(getId(selectedRole));

                return (
                  <button
                    type="button"
                    key={getId(role) ?? name}
                    className={`roles-reference-role${active ? " active" : ""}`}
                    onClick={() => chooseRole(role)}
                  >
                    <span>
                      <p className="roles-reference-role-name">{name}</p>
                      <p className="roles-reference-role-description">
                        {role.description ||
                          (normalize(name) === "admin"
                            ? "Full access, delete-protected"
                            : normalize(name) === "manager"
                              ? "Manage users, view roles"
                              : normalize(name) === "viewer"
                                ? "Read-only access"
                                : "Describe this role")}
                      </p>
                    </span>

                    <span className="roles-reference-count">
                      {userCount(role)} users
                    </span>
                  </button>
                );
              })
            )}
          </aside>

          <section className="roles-reference-detail">
            {!selectedRole ? (
              <p className="roles-reference-subtitle">
                {loading ? "Loading role details…" : "No roles available."}
              </p>
            ) : (
              <>
                <div className="roles-reference-detail-head">
                  <div>
                    <h2>{selectedRoleName}</h2>
                    <p>
                      {selectedRole.description ||
                        (normalize(selectedRoleName) === "admin"
                          ? "Full access, delete-protected"
                          : normalize(selectedRoleName) === "manager"
                            ? "Manage users, view roles"
                            : normalize(selectedRoleName) === "viewer"
                              ? "Read-only access"
                              : "Describe this role")}
                    </p>
                  </div>

                  {!isSystemRole && (
                    <div className="roles-reference-actions">
                      <button
                        type="button"
                        className="roles-reference-secondary"
                        onClick={openEdit}
                      >
                        Edit role
                      </button>

                      <button
                        type="button"
                        className="roles-reference-secondary"
                        onClick={removeRole}
                      >
                        Delete role
                      </button>
                    </div>
                  )}
                </div>

                {loadingRolePermissions ? (
                  <p className="roles-reference-subtitle">
                    Loading assigned permissions…
                  </p>
                ) : (
                  ["USERS", "ROLES", "AUDIT"].map((group) => {
                    const items = permissionItems.filter(
                      (item) => item.group === group
                    );

                    if (!items.length) return null;

                    return (
                      <div className="roles-reference-group" key={group}>
                        <h3 className="roles-reference-group-title">
                          {GROUPS[group]}
                        </h3>

                        <div className="roles-reference-permission-grid">
                          {items.map((item) => {
                            const checked = selectedPermissions.includes(
                              item.code
                            );

                            const permissionStyle = {
                              width: "100%",
                              minWidth: 0,
                              minHeight: "60px",
                              display: "flex",
                              alignItems: "center",
                              gap: "11px",
                              padding: "11px 13px",
                              boxSizing: "border-box",
                              borderRadius: "10px",
                              textAlign: "left",
                              fontFamily: "inherit",
                              cursor: "pointer",
                              backgroundColor: checked
                                ? "#f3f9f8"
                                : "#ffffff",
                              border: checked
                                ? "1px solid #218f86"
                                : "1px solid #dfe5ed",
                              color: "#000000",
                            };

                            const checkboxStyle = {
                              width: "20px",
                              height: "20px",
                              minWidth: "20px",
                              boxSizing: "border-box",
                              display: "inline-flex",
                              alignItems: "center",
                              justifyContent: "center",
                              border: checked
                                ? "1px solid #0e8179"
                                : "1px solid #cbd5e1",
                              borderRadius: "5px",
                              backgroundColor: checked
                                ? "#0e8179"
                                : "#ffffff",
                              color: "#ffffff",
                              fontSize: "15px",
                              fontWeight: 800,
                              lineHeight: 1,
                            };

                            return (
                              <button
                                type="button"
                                key={item.code}
                                onClick={() => togglePermission(item.code)}
                                className="roles-reference-permission"
                                aria-pressed={checked}
                                disabled={
                                  savingPermissions ||
                                  loadingRolePermissions
                                }
                                style={permissionStyle}
                              >
                                <span
                                  aria-hidden="true"
                                  style={checkboxStyle}
                                >
                                  {checked ? "✓" : ""}
                                </span>

                                <span style={{ minWidth: 0 }}>
                                  <p className="roles-reference-code">
                                    {item.code}
                                  </p>
                                  <p className="roles-reference-description">
                                    {item.description}
                                  </p>
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })
                )}
              </>
            )}
          </section>
        </section>

        {modal && (
          <div
            className="roles-reference-modal-backdrop"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) {
                setModal(null);
              }
            }}
          >
            <form className="roles-reference-modal" onSubmit={submitRole}>
              <h2>Edit role</h2>

              <label className="roles-reference-field">
                Role name
                <input
                  value={roleName}
                  onChange={(event) => setRoleName(event.target.value)}
                  placeholder="e.g. Project Manager"
                  required
                  autoFocus
                />
              </label>

              <label className="roles-reference-field">
                Description
                <textarea
                  value={roleDescription}
                  onChange={(event) =>
                    setRoleDescription(event.target.value)
                  }
                  placeholder="Describe this role's access"
                  rows={3}
                />
              </label>

              <div className="roles-reference-modal-actions">
                <button
                  type="button"
                  className="roles-reference-secondary"
                  onClick={() => setModal(null)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="roles-reference-primary"
                  disabled={savingRole}
                >
                  {savingRole ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

export default Roles;
