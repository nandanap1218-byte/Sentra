
import { useEffect, useMemo, useState } from "react";
import Sidebar from "../components/Sidebar";
import apiClient from "../api/apiClient";
import {
  getUsers,
  createUser,
  updateUser,
  getUserRoles,
  updateUserRoles,
} from "../api/users";
import { getRoles } from "../api/roles";

const PAGE_SIZE = 4;

const COLORS = [
  "#bd6269",
  "#b5812e",
  "#7546b3",
  "#596575",
  "#16877e",
  "#2878b5",
];

const emptyForm = {
  full_name: "",
  email: "",
  is_active: true,
};

function initials(user) {
  return (user?.full_name || user?.email || "U")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");
}

function roleNames(user) {
  const roles = Array.isArray(user?.roles) ? user.roles : [];

  return roles.map((role) =>
    typeof role === "string"
      ? role
      : role?.name || role?.role_name || role?.role?.name || "Role"
  );
}

function getRoleId(role) {
  if (typeof role === "string") return role;

  return String(
    role?.id ?? role?.role_id ?? role?.role?.id ?? role?.uuid ?? ""
  );
}

function getRoleName(role) {
  if (typeof role === "string") return role;

  return (
    role?.name ??
    role?.role_name ??
    role?.role?.name ??
    role?.title ??
    "Role"
  );
}

function unwrapList(response, keys = []) {
  const data = response?.data ?? response;

  if (Array.isArray(data)) return data;

  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key];
  }

  if (Array.isArray(data?.results)) return data.results;

  return [];
}

function normalizeRoleName(name) {
  return String(name || "").trim().toLowerCase();
}

function lastLogin(user) {
  const value =
    user?.last_login ?? user?.lastLogin ?? user?.last_login_at ?? null;

  if (!value) return "Never";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Unavailable";

  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

export default function Users() {
  const [users, setUsers] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [toggleLoading, setToggleLoading] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);

  const [availableRoles, setAvailableRoles] = useState([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState([]);
  const [rolesLoading, setRolesLoading] = useState(false);

  // Permissions of the currently signed-in user.
  const [canCreateUsers, setCanCreateUsers] = useState(false);
  const [canEditUsers, setCanEditUsers] = useState(false);
  const [canAssignRoles, setCanAssignRoles] = useState(false);
  const [permissionsLoading, setPermissionsLoading] = useState(true);

  // Load current-user permissions. Fail closed if this request fails.
  useEffect(() => {
    let cancelled = false;

    async function loadCurrentUserPermissions() {
      setPermissionsLoading(true);

      try {
        const response = await apiClient.get("/me/");
        const data = response?.data ?? response;

        const permissions = Array.isArray(data?.permissions)
          ? data.permissions
          : [];

        if (!cancelled) {
          setCanCreateUsers(permissions.includes("users.create"));
          setCanEditUsers(permissions.includes("users.edit"));
          setCanAssignRoles(
            permissions.includes("users.roles.assign")
          );
        }
      } catch (err) {
        console.error(
          "Unable to load current-user permissions:",
          err
        );

        if (!cancelled) {
          setCanCreateUsers(false);
          setCanEditUsers(false);
          setCanAssignRoles(false);
        }
      } finally {
        if (!cancelled) {
          setPermissionsLoading(false);
        }
      }
    }

    loadCurrentUserPermissions();

    return () => {
      cancelled = true;
    };
  }, []);

  async function loadUsers(nextPage = page) {
    setLoading(true);
    setError("");

    try {
      const response = await getUsers({
        search,
        isActive: statusFilter,
        page: nextPage,
        pageSize: PAGE_SIZE,
        ordering: sortAsc ? "full_name" : "-full_name",
      });

      const results = unwrapList(response, ["users"]);
      const data = response?.data ?? response;
      const total = Number(data?.count ?? results.length);
      const calculatedPages = Math.max(
        1,
        Math.ceil(total / PAGE_SIZE)
      );

      setUsers(results);
      setCount(total);
      setTotalPages(calculatedPages);

      if (nextPage > calculatedPages) {
        setPage(calculatedPages);
      }
    } catch (err) {
      console.error("Failed to load SENTRA users:", err);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load users."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search, statusFilter, sortAsc]);

  const filteredUsers = useMemo(
    () =>
      roleFilter
        ? users.filter((user) =>
            roleNames(user).includes(roleFilter)
          )
        : users,
    [users, roleFilter]
  );

  const allDisplayedRoleNames = useMemo(() => {
    const names = users.flatMap(roleNames);
    return [...new Set(names)].sort((a, b) => a.localeCompare(b));
  }, [users]);

  const firstItem =
    count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastItem = Math.min(page * PAGE_SIZE, count);

  async function openCreate() {
    if (permissionsLoading || !canCreateUsers) {
      setError("You do not have permission to create users.");
      return;
    }

    setEditingUser(null);
    setForm({ ...emptyForm });
    setSelectedRoleIds([]);
    setAvailableRoles([]);
    setShowForm(true);
    setError("");

    // Only users with users.roles.assign can load and assign roles.
    if (!canAssignRoles) {
      setRolesLoading(false);
      return;
    }

    setRolesLoading(true);

    try {
      const response = await getRoles();
      setAvailableRoles(unwrapList(response, ["roles"]));
    } catch (err) {
      console.error("Unable to load roles:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load roles. Please check the roles API."
      );
    } finally {
      setRolesLoading(false);
    }
  }

  async function openEdit(user) {
    if (permissionsLoading || !canEditUsers) {
      setError("You do not have permission to edit users.");
      return;
    }

    setEditingUser(user);
    setForm({
      full_name: user.full_name || "",
      email: user.email || "",
      is_active: Boolean(user.is_active),
    });
    setSelectedRoleIds([]);
    setAvailableRoles([]);
    setShowForm(true);
    setError("");

    // Role assignment is independent of roles.manage.
    if (!canAssignRoles) {
      setRolesLoading(false);
      return;
    }

    setRolesLoading(true);

    try {
      const [rolesResponse, assignedResponse] = await Promise.all([
        getRoles(),
        getUserRoles(user.id),
      ]);

      const roles = unwrapList(rolesResponse, ["roles"]);
      setAvailableRoles(roles);

      const resolveRoleId = (item) => {
        if (
          typeof item === "string" ||
          typeof item === "number"
        ) {
          const value = String(item);

          const match = roles.find(
            (role) =>
              getRoleId(role) === value ||
              normalizeRoleName(getRoleName(role)) ===
                normalizeRoleName(value)
          );

          return match ? getRoleId(match) : "";
        }

        if (!item || typeof item !== "object") return "";

        const possibleId = String(
          item.role_id ??
            item.role?.id ??
            item.role?.uuid ??
            (typeof item.role === "string" ||
            typeof item.role === "number"
              ? item.role
              : undefined) ??
            item.id ??
            item.uuid ??
            ""
        );

        const matchById = roles.find(
          (role) => getRoleId(role) === possibleId
        );

        if (matchById) return getRoleId(matchById);

        const possibleName =
          item.role_name ??
          item.role?.name ??
          item.name ??
          item.title;

        if (possibleName) {
          const matchByName = roles.find(
            (role) =>
              normalizeRoleName(getRoleName(role)) ===
              normalizeRoleName(possibleName)
          );

          if (matchByName) return getRoleId(matchByName);
        }

        return "";
      };

      let assigned = [];
      const assignedData =
        assignedResponse?.data ?? assignedResponse;

      if (Array.isArray(assignedData)) {
        assigned = assignedData;
      } else if (Array.isArray(assignedData?.roles)) {
        assigned = assignedData.roles;
      } else if (Array.isArray(assignedData?.role_ids)) {
        assigned = assignedData.role_ids;
      } else if (Array.isArray(assignedData?.results)) {
        assigned = assignedData.results;
      }

      let assignedIds = assigned
        .map(resolveRoleId)
        .filter(Boolean);

      if (
        assignedIds.length === 0 &&
        Array.isArray(user.roles)
      ) {
        assignedIds = user.roles
          .map(resolveRoleId)
          .filter(Boolean);
      }

      setSelectedRoleIds([...new Set(assignedIds)]);
    } catch (err) {
      console.error("Unable to load user roles:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load assigned roles. Available roles will still be loaded."
      );

      try {
        const response = await getRoles();
        setAvailableRoles(unwrapList(response, ["roles"]));
      } catch (roleError) {
        console.error(
          "Unable to load available roles:",
          roleError
        );
      }
    } finally {
      setRolesLoading(false);
    }
  }

  function closeForm() {
    if (saving) return;

    setShowForm(false);
    setEditingUser(null);
    setForm({ ...emptyForm });
    setSelectedRoleIds([]);
    setAvailableRoles([]);
    setError("");
  }

  function updateForm(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: name === "is_active" ? value === "true" : value,
    }));
  }

  function toggleRole(role) {
    if (!canAssignRoles) return;

    const id = getRoleId(role);
    if (!id) return;

    setSelectedRoleIds((current) =>
      current.includes(id)
        ? current.filter((roleId) => roleId !== id)
        : [...current, id]
    );
  }

  async function submitForm(event) {
    event.preventDefault();

    if (saving || permissionsLoading) return;

    if (editingUser && !canEditUsers) {
      setError("You do not have permission to edit users.");
      return;
    }

    if (!editingUser && !canCreateUsers) {
      setError("You do not have permission to create users.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        is_active: form.is_active,
      };

      if (editingUser) {
        await updateUser(editingUser.id, payload);

        // Never send a role update without users.roles.assign.
        if (canAssignRoles) {
          await updateUserRoles(
            editingUser.id,
            selectedRoleIds
          );
        }
      } else {
        // Password is intentionally not collected or sent here.
        const createResponse = await createUser(payload);
        const createdData =
          createResponse?.data ?? createResponse;
        const createdUser =
          createdData?.user ?? createdData;
        const createdId = createdUser?.id;

        if (
          canAssignRoles &&
          selectedRoleIds.length > 0
        ) {
          if (!createdId) {
            throw new Error(
              "The user may have been created, but the API response did not include the new user's ID. Please check the Users list."
            );
          }

          await updateUserRoles(
            createdId,
            selectedRoleIds
          );
        }
      }

      setShowForm(false);
      setEditingUser(null);
      setForm({ ...emptyForm });
      setSelectedRoleIds([]);
      setAvailableRoles([]);

      await loadUsers(page);
    } catch (err) {
      console.error("Unable to save user:", err);

      console.log(
        "Backend response:",
        JSON.stringify(err?.response?.data ?? {}, null, 2)
      );

      const data = err?.response?.data;

      setError(
        data?.detail ||
          data?.role_ids?.[0] ||
          data?.email?.[0] ||
          data?.full_name?.[0] ||
          err?.message ||
          "Unable to save user."
      );
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(user) {
    if (permissionsLoading || !canEditUsers) {
      setError("You do not have permission to change user status.");
      return;
    }

    setToggleLoading(user.id);
    setError("");

    try {
      await updateUser(user.id, {
        is_active: !user.is_active,
      });

      await loadUsers(page);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to update status."
      );
    } finally {
      setToggleLoading(null);
    }
  }

  function exportCsv() {
    const rows = [
      ["Name", "Email", "Roles", "Status", "Last Login"],
      ...filteredUsers.map((user) => [
        user.full_name || "",
        user.email || "",
        roleNames(user).join(", "),
        user.is_active ? "Active" : "Inactive",
        lastLogin(user),
      ]),
    ];

    const csv = rows
      .map((row) =>
        row
          .map((value) =>
            `"${String(value).replace(/"/g, '""')}"`
          )
          .join(",")
      )
      .join("\r\n");

    const blob = new Blob(["\uFEFF", csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "sentra-users.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  return (
    <div className="dashboard-layout sentra-users-page">
      <style>{`
        .sentra-users-page { min-height: 100vh; background: #f5f7fa; color: #101827; }
        .sentra-users-page .dashboard-content { box-sizing: border-box; min-width: 0; width: 100%; padding: 26px 40px 36px; background: #f5f7fa; }
        .sentra-users-page button, .sentra-users-page input, .sentra-users-page select { font: inherit; }
        .sentra-users-page .users-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin: 0 0 22px; }
        .sentra-users-page .users-heading h1 { margin: 0 0 4px; font-size: 27px; line-height: 1.25; font-weight: 700; letter-spacing: -.4px; color: #111827; }
        .sentra-users-page .users-heading p { margin: 0; color: #64748b; font-size: 14px; }
        .sentra-users-page .add-user-btn { border: 0; background: #117c76; color: white; font-size: 14px; font-weight: 650; padding: 13px 20px; border-radius: 9px; min-height: 45px; cursor: pointer; white-space: nowrap; }
        .sentra-users-page .users-toolbar { display: flex; align-items: center; gap: 11px; margin-bottom: 16px; }
        .sentra-users-page .users-search { flex: 1 1 320px; max-width: 354px; min-width: 150px; }
        .sentra-users-page .users-search, .sentra-users-page .users-toolbar select { box-sizing: border-box; height: 45px; background: #fff; border: 1px solid #d5dce6; border-radius: 10px; color: #334155; padding: 0 14px; outline: none; font-size: 14px; }
        .sentra-users-page .users-search:focus, .sentra-users-page .users-toolbar select:focus { border-color: #117c76; box-shadow: 0 0 0 3px rgba(17,124,118,.1); }
        .sentra-users-page .users-search::placeholder { color: #9aa9bf; }
        .sentra-users-page .users-toolbar select { min-width: 107px; }
        .sentra-users-page .toolbar-spacer { flex: 1; }
        .sentra-users-page .export-btn { height: 45px; border: 1px solid #d5dce6; background: #fff; border-radius: 10px; color: #1f2937; padding: 0 17px; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
        .sentra-users-page .export-btn:hover, .sentra-users-page .action-btn:hover, .sentra-users-page .pagination-controls button:not(:disabled):hover { background: #f8fafc; }
        .sentra-users-page .users-card { overflow: hidden; border: 1px solid #dfe5ed; border-radius: 12px; background: #fff; }
        .sentra-users-page .users-table { width: 100%; border-collapse: collapse; table-layout: auto; }
        .sentra-users-page .users-table thead th { height: 41px; padding: 0 22px; border-bottom: 1px solid #e1e6ed; color: #8190a6; text-transform: uppercase; letter-spacing: .65px; font-size: 11px; font-weight: 700; text-align: left; white-space: nowrap; }
        .sentra-users-page .users-table thead th:last-child { text-align: right; }
        .sentra-users-page .users-table tbody tr { border-bottom: 1px solid #edf0f4; }
        .sentra-users-page .users-table tbody tr:last-child { border-bottom: 0; }
        .sentra-users-page .users-table tbody td { height: 65px; padding: 0 22px; font-size: 13px; color: #334155; white-space: nowrap; }
        .sentra-users-page .identity { display: flex; align-items: center; gap: 12px; min-width: 220px; }
        .sentra-users-page .avatar { display: flex; align-items: center; justify-content: center; width: 37px; height: 37px; flex: 0 0 37px; border-radius: 50%; color: white; font-weight: 700; font-size: 12px; }
        .sentra-users-page .identity-copy { display: flex; flex-direction: column; gap: 3px; }
        .sentra-users-page .identity-copy strong { color: #111827; font-size: 14px; font-weight: 650; }
        .sentra-users-page .identity-copy span { color: #8190a6; font-size: 12px; }
        .sentra-users-page .role-pill { display: inline-block; border-radius: 20px; background: #edf6f5; color: #087e80; padding: 5px 11px; font-size: 12px; font-weight: 650; margin: 2px 4px 2px 0; }
        .sentra-users-page .status { font-weight: 650; font-size: 13px; }
        .sentra-users-page .status:before { content: ""; display: inline-block; width: 6px; height: 6px; margin: 0 6px 1px 0; border-radius: 50%; background: #078579; }
        .sentra-users-page .status.inactive { color: #c72525; }
        .sentra-users-page .status.active { color: #087e80; }
        .sentra-users-page .status.inactive:before { background: #d52b2b; }
        .sentra-users-page .last-login { color: #64748b !important; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px !important; white-space: nowrap; }
        .sentra-users-page .actions { display: flex; align-items: center; justify-content: flex-end; gap: 9px; }
        .sentra-users-page .action-btn { background: #fff; border: 1px solid #d5dce6; color: #1f2937; border-radius: 8px; height: 34px; padding: 0 14px; cursor: pointer; font-size: 12px; font-weight: 600; }
        .sentra-users-page .action-btn.deactivate { color: #c21f25; }
        .sentra-users-page .action-btn.activate { color: #087e80; }
        .sentra-users-page .action-btn:disabled { opacity: .55; cursor: wait; }
        .sentra-users-page .table-message { padding: 25px !important; text-align: center; color: #64748b !important; }
        .sentra-users-page .users-footer { min-height: 62px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; justify-content: space-between; gap: 18px; border-top: 1px solid #edf0f4; color: #64748b; font-size: 13px; }
        .sentra-users-page .pagination-info { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
        .sentra-users-page .pagination-note { color: #9aa9bf; font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
        .sentra-users-page .pagination-controls { display: flex; align-items: center; gap: 12px; }
        .sentra-users-page .pagination-controls button { height: 35px; padding: 0 14px; border: 1px solid #d5dce6; border-radius: 8px; background: white; color: #334155; cursor: pointer; font-size: 13px; }
        .sentra-users-page .pagination-controls button:disabled { color: #bdc7d5; cursor: default; }
        .sentra-users-page .page-count { color: #111827; font-weight: 650; white-space: nowrap; }
        .sentra-users-page .users-error { margin: 0 0 14px; padding: 10px 13px; border: 1px solid #fecaca; border-radius: 8px; background: #fff1f2; color: #b91c1c; font-size: 13px; }
        .sentra-users-page .edit-modal-overlay { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px; background: rgba(15,23,42,.48); backdrop-filter: blur(3px); overflow-y: auto; }
        .sentra-users-page .edit-modal { width: 100%; max-width: 650px; max-height: calc(100vh - 40px); overflow-y: auto; box-sizing: border-box; padding: 27px; border: 1px solid #e4e9f0; border-radius: 16px; background: #fff; box-shadow: 0 24px 80px rgba(15,23,42,.2); animation: sentra-modal-in .18s ease-out; }
        @keyframes sentra-modal-in { from { opacity: 0; transform: translateY(8px) scale(.99); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .sentra-users-page .edit-modal-header { display: flex; align-items: center; justify-content: flex-start; margin-bottom: 23px; }
        .sentra-users-page .edit-modal-header h2 { margin: 0; color: #111827; font-size: 23px; font-weight: 750; letter-spacing: -.4px; }
        .sentra-users-page .edit-fields { display: grid; grid-template-columns: 1fr; gap: 17px; }
        .sentra-users-page .edit-field { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
        .sentra-users-page .edit-field > label, .sentra-users-page .roles-label { color: #344054; font-size: 13px; font-weight: 650; }
        .sentra-users-page .edit-field input { box-sizing: border-box; width: 100%; height: 44px; padding: 0 13px; border: 1px solid #d9e0e9; border-radius: 9px; background: #fff; color: #182230; font-size: 14px; outline: none; transition: border-color .15s, box-shadow .15s; }
        .sentra-users-page .edit-field input:focus { border-color: #117c76; box-shadow: 0 0 0 3px rgba(17,124,118,.1); }
        .sentra-users-page .roles-section { margin-top: 21px; width: 100%; min-width: 0; }
        .sentra-users-page .roles-label { display: block; margin-bottom: 12px; }
        .sentra-users-page .role-options { display: flex; flex-flow: row nowrap; align-items: center; gap: 8px; width: 100%; min-width: 0; overflow: hidden; }
        .sentra-users-page .role-option { display: inline-flex; flex: 1 1 0; min-width: 0; align-items: center; justify-content: center; min-height: 40px; padding: 0 10px; border: 1px solid #9ca3af; border-radius: 999px; background: #fff; color: #6b7280; font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; user-select: none; transition: background .15s, border-color .15s, color .15s; }
        .sentra-users-page .role-option:hover { background: #f3f4f6; border-color: #6b7280; color: #4b5563; }
        .sentra-users-page .role-option.selected { border-color: #117c76; background: #117c76; color: #fff; }
        .sentra-users-page .role-option:disabled { opacity: .6; cursor: wait; }
        .sentra-users-page .roles-loading { color: #64748b; font-size: 13px; }
        .sentra-users-page .edit-modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 27px; padding-top: 19px; border-top: 1px solid #edf0f4; }
        .sentra-users-page .modal-cancel, .sentra-users-page .modal-save { min-height: 42px; padding: 0 18px; border-radius: 9px; font-size: 13px; font-weight: 650; cursor: pointer; }
        .sentra-users-page .modal-cancel { border: 1px solid #d9e0e9; background: #fff; color: #344054; }
        .sentra-users-page .modal-cancel:hover { background: #f8fafc; }
        .sentra-users-page .modal-save { border: 1px solid #117c76; background: #117c76; color: white; box-shadow: 0 2px 4px rgba(17,124,118,.12); }
        .sentra-users-page .modal-save:hover { background: #0c6d67; }
        .sentra-users-page .modal-cancel:disabled, .sentra-users-page .modal-save:disabled { opacity: .6; cursor: wait; }
        .sentra-users-page .modal-error { margin-top: 16px; margin-bottom: 0; }
        @media (max-width: 1050px) {
          .sentra-users-page .dashboard-content { padding: 24px; }
          .sentra-users-page .users-card { overflow-x: auto; }
          .sentra-users-page .users-table { min-width: 900px; }
        }
        @media (max-width: 650px) {
          .sentra-users-page .dashboard-content { padding: 20px 14px; }
          .sentra-users-page .users-toolbar { flex-wrap: wrap; }
          .sentra-users-page .users-search { max-width: none; flex-basis: 100%; }
          .sentra-users-page .toolbar-spacer { display: none; }
          .sentra-users-page .users-footer { align-items: flex-start; flex-direction: column; padding: 14px; }
          .sentra-users-page .edit-modal-overlay { padding: 12px; }
          .sentra-users-page .edit-modal { padding: 21px; max-height: calc(100vh - 24px); }
          .sentra-users-page .edit-modal-header h2 { font-size: 21px; }
          .sentra-users-page .role-options { gap: 5px; }
          .sentra-users-page .role-option { min-height: 36px; padding: 0 5px; font-size: 10px; }
          .sentra-users-page .edit-modal-footer { gap: 8px; }
          .sentra-users-page .modal-cancel, .sentra-users-page .modal-save { padding: 0 13px; }
        }
      `}</style>

      <Sidebar />

      <main className="dashboard-content">
        <header className="users-heading">
          <div>
            <h1>Users</h1>
            <p>{count} users found</p>
          </div>

          {!permissionsLoading && canCreateUsers && (
            <button
              className="add-user-btn"
              type="button"
              onClick={
                showForm && !editingUser ? closeForm : openCreate
              }
            >
              {showForm && !editingUser ? "Cancel" : "+ Add user"}
            </button>
          )}
        </header>

        <div className="users-toolbar">
          <input
            className="users-search"
            type="search"
            value={search}
            placeholder="Search by name or email..."
            onChange={(event) => {
              setPage(1);
              setSearch(event.target.value);
            }}
          />

          <select
            aria-label="Filter by role"
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value)}
          >
            <option value="">All roles</option>
            {allDisplayedRoleNames.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>

          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(event) => {
              setPage(1);
              setStatusFilter(event.target.value);
            }}
          >
            <option value="">All statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>

          <div className="toolbar-spacer" />

          <button
            className="export-btn"
            type="button"
            onClick={exportCsv}
          >
            ↓ &nbsp; Export to Excel
          </button>
        </div>

        {error && !showForm && (
          <div className="users-error" role="alert">
            {error}
          </div>
        )}

        <section className="users-card">
          <table className="users-table">
            <thead>
              <tr>
                <th>
                  <button
                    type="button"
                    onClick={() => {
                      setPage(1);
                      setSortAsc((value) => !value);
                    }}
                    style={{
                      border: 0,
                      background: "transparent",
                      padding: 0,
                      color: "inherit",
                      font: "inherit",
                      letterSpacing: "inherit",
                      textTransform: "inherit",
                      cursor: "pointer",
                    }}
                  >
                    User {sortAsc ? "↑" : "↓"}
                  </button>
                </th>
                <th>Roles</th>
                <th>Status</th>
                <th>Last login</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td className="table-message" colSpan={5}>
                    Loading users...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td className="table-message" colSpan={5}>
                    No users found.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user, index) => (
                  <tr key={user.id}>
                    <td>
                      <div className="identity">
                        <div
                          className="avatar"
                          style={{
                            backgroundColor:
                              COLORS[
                                ((page - 1) * PAGE_SIZE + index) %
                                  COLORS.length
                              ],
                          }}
                        >
                          {initials(user)}
                        </div>

                        <div className="identity-copy">
                          <strong>
                            {user.full_name || "Unnamed user"}
                          </strong>
                          <span>{user.email}</span>
                        </div>
                      </div>
                    </td>

                    <td>
                      {roleNames(user).length ? (
                        roleNames(user).map((role, roleIndex) => (
                          <span
                            className="role-pill"
                            key={`${user.id}-${role}-${roleIndex}`}
                          >
                            {role}
                          </span>
                        ))
                      ) : (
                        <span style={{ color: "#94a3b8" }}>—</span>
                      )}
                    </td>

                    <td>
                      <span
                        className={`status ${
                          user.is_active ? "active" : "inactive"
                        }`}
                      >
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>

                    <td className="last-login">
                      {lastLogin(user)}
                    </td>

                    <td>
                      <div className="actions">
                        {!permissionsLoading && canEditUsers && (
                          <button
                            className="action-btn"
                            type="button"
                            onClick={() => openEdit(user)}
                          >
                            Edit
                          </button>
                        )}

                        {!permissionsLoading && canEditUsers && (
                          <button
                            className={`action-btn ${
                              user.is_active
                                ? "deactivate"
                                : "activate"
                            }`}
                            type="button"
                            disabled={toggleLoading === user.id}
                            onClick={() => toggleStatus(user)}
                          >
                            {toggleLoading === user.id
                              ? "Working..."
                              : user.is_active
                                ? "Deactivate"
                                : "Activate"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <footer className="users-footer">
            <div className="pagination-info">
              <span>
                Showing {firstItem}–{lastItem} of {count}
              </span>
              <span className="pagination-note">
                server-side · page_size={PAGE_SIZE}
              </span>
            </div>

            <div className="pagination-controls">
              <button
                type="button"
                onClick={() =>
                  setPage((value) => Math.max(1, value - 1))
                }
                disabled={page <= 1 || loading}
              >
                ← Prev
              </button>

              <span className="page-count">
                {page} / {totalPages}
              </span>

              <button
                type="button"
                onClick={() =>
                  setPage((value) =>
                    Math.min(totalPages, value + 1)
                  )
                }
                disabled={page >= totalPages || loading}
              >
                Next →
              </button>
            </div>
          </footer>
        </section>
      </main>

      {showForm && (
        <div
          className="edit-modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeForm();
            }
          }}
        >
          <section
            className="edit-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="user-modal-title"
          >
            <header className="edit-modal-header">
              <h2 id="user-modal-title">
                {editingUser ? "Edit user" : "Add user"}
              </h2>
            </header>

            <form onSubmit={submitForm}>
              <div className="edit-fields">
                <div className="edit-field">
                  <label htmlFor="user-full-name">Full name</label>
                  <input
                    id="user-full-name"
                    name="full_name"
                    value={form.full_name}
                    onChange={updateForm}
                    placeholder="Enter full name"
                    autoComplete="name"
                    required
                  />
                </div>

                <div className="edit-field">
                  <label htmlFor="user-email">Email</label>
                  <input
                    id="user-email"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={updateForm}
                    placeholder="Enter email address"
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              {/* Role controls are visible only with users.roles.assign. */}
              {canAssignRoles && (
                <div className="roles-section">
                  <span className="roles-label">Roles</span>

                  {rolesLoading ? (
                    <div className="roles-loading">
                      Loading roles...
                    </div>
                  ) : availableRoles.length === 0 ? (
                    <div className="roles-loading">
                      No roles available. Check the roles API.
                    </div>
                  ) : (
                    <div className="role-options">
                      {availableRoles.map((role, index) => {
                        const id = getRoleId(role);
                        const name = getRoleName(role);
                        const checked =
                          selectedRoleIds.includes(id);

                        return (
                          <button
                            key={id || `${name}-${index}`}
                            className={`role-option ${
                              checked ? "selected" : ""
                            }`}
                            type="button"
                            aria-pressed={checked}
                            disabled={
                              rolesLoading || saving || !id
                            }
                            onClick={() => toggleRole(role)}
                            title={name}
                          >
                            {name}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {error && (
                <div
                  className="users-error modal-error"
                  role="alert"
                >
                  {error}
                </div>
              )}

              <footer className="edit-modal-footer">
                <button
                  className="modal-cancel"
                  type="button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  className="modal-save"
                  type="submit"
                  disabled={saving || rolesLoading || permissionsLoading}
                >
                  {saving
                    ? editingUser
                      ? "Saving..."
                      : "Creating..."
                    : editingUser
                      ? "Save changes"
                      : "Create user"}
                </button>
              </footer>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
