import { useEffect, useMemo, useState } from "react";

import Sidebar from "../components/Sidebar";

import apiClient from "../api/apiClient";



const PAGE_SIZE = 6;



function getActor(log) {
  const metadata = log.metadata ?? log.extra_data ?? log.details ?? {};
  const metadataEmail =
    metadata && typeof metadata === "object"
      ? metadata.email ?? metadata.actor_email ?? metadata.user_email
      : null;

  // Prefer the actual user email when the backend only labels the event "System".
  const directEmail =
    log.actor_email ??
    log.user_email ??
    log.created_by_email ??
    log.performed_by_email ??
    (typeof metadataEmail === "string" ? metadataEmail : null);
  if (directEmail) return directEmail;

  const actor =
    log.actor ??
    log.user ??
    log.created_by ??
    log.performed_by ??
    log.performed_by_user;

  if (actor && typeof actor === "object") {
    return (
      actor.email ||
      actor.full_name ||
      actor.name ||
      actor.username ||
      actor.id ||
      "System"
    );
  }

  if (typeof actor === "string" && actor.trim() && actor.toLowerCase() !== "system") {
    return actor;
  }

  return (
    log.actor_name ||
    log.user_name ||
    log.created_by_name ||
    log.performed_by_name ||
    (typeof actor === "string" && actor.trim() ? actor : "System")
  );
}

function getDetail(log) {
  const metadata = log.metadata ?? log.extra_data ?? log.details ?? {};
  const data =
    metadata && typeof metadata === "object" && !Array.isArray(metadata)
      ? metadata
      : {};
  const action = String(
    log.action || log.event_type || log.event || log.action_type || ""
  ).toLowerCase().replaceAll("_", ".");

  const directDetail =
    log.detail ?? log.description ?? log.message ??
    data.detail ?? data.description ?? data.message;

  const valueText = (value) => {
    if (value === null || value === undefined || value === "") return "";
    if (typeof value === "string") return value;
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  };

  const firstValue = (...values) =>
    values.find((value) => value !== null && value !== undefined && value !== "");

  const ip = firstValue(
    data.ip_address, data.ip, data.remote_addr, data.client_ip, data.request_ip
  );
  const email = firstValue(
    data.target_email, data.email, data.user_email, data.created_email,
    data.updated_email, data.target_user_email
  );
  const roleName = firstValue(
    data.role_name, data.target_role_name,
    typeof data.role === "string" ? data.role : null,
    data.role_title, data.name
  );
  const targetName = firstValue(
    data.full_name, data.target_name, data.user_name, data.target_user_name
  );

  const parseList = (value) => {
    if (Array.isArray(value)) return value;
    if (typeof value === "string") {
      try {
        const parsed = JSON.parse(value);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  };

  const before = parseList(data.before);
  const after = parseList(data.after);
  const itemName = (item) =>
    typeof item === "string"
      ? item
      : firstValue(item?.codename, item?.name, item?.email, item?.full_name, item?.id);

  const beforeNames = before.map(itemName).filter(Boolean);
  const afterNames = after.map(itemName).filter(Boolean);
  const added = afterNames.filter((name) => !beforeNames.includes(name));
  const removed = beforeNames.filter((name) => !afterNames.includes(name));
  const target = targetName || email;

  if (action.includes("login")) return ip ? `Signed in from ${ip}` : "Signed in";
  if (action.includes("logout")) return ip ? `Signed out from ${ip}` : "Signed out";

  if (action.includes("role.permissions.update")) {
    const role = firstValue(data.role_name, data.name, roleName, "role");
    if (added.length) return `Added ${added.join(", ")} to ${role}`;
    if (removed.length) return `Removed ${removed.join(", ")} from ${role}`;
    return `Updated permissions for ${role}`;
  }

  if (action.includes("user.roles.update") || action.includes("role.assign")) {
    const newRole = afterNames[0] || roleName;
    if (newRole && target) return `Assigned ${newRole} role to ${target}`;
    if (newRole) return `Assigned ${newRole} role`;
    return "Updated user role assignments";
  }

  if (action.includes("role.create")) {
    const name = firstValue(data.role_name, data.name, roleName, directDetail);
    return name ? `Created role ${valueText(name)}` : "Created a role";
  }
  if (action.includes("role.delete") || action.includes("role.remove")) {
    const name = firstValue(data.role_name, data.name, roleName, directDetail);
    return name ? `Deleted role ${valueText(name)}` : "Deleted a role";
  }
  if (action.includes("role.update")) {
    if (added.length) return `Added ${added.join(", ")} to ${roleName || "role"}`;
    const name = firstValue(data.role_name, data.name, roleName);
    return name ? `Updated role ${valueText(name)}` : "Updated a role";
  }

  if (action.includes("user.create") || action.includes("register")) {
    const created = firstValue(email, targetName, typeof directDetail === "string" ? directDetail : null);
    return created ? `Created user ${valueText(created)}` : "Created a user";
  }
  if (action.includes("user.deactivate") || action.includes("user.disable")) {
    return email ? `Deactivated ${email}` : target ? `Deactivated ${target}` : "Deactivated a user";
  }
  if (action.includes("user.activate") || action.includes("user.enable")) {
    return email ? `Activated ${email}` : target ? `Activated ${target}` : "Activated a user";
  }
  if (action.includes("user.delete")) {
    return email ? `Deleted user ${email}` : target ? `Deleted user ${target}` : "Deleted a user";
  }
  if (action.includes("user.update")) {
    if (directDetail && typeof directDetail === "string" && !directDetail.trim().startsWith("{")) {
      return directDetail;
    }
    return target ? `Updated user ${target}` : "Updated a user";
  }

  if (directDetail !== null && directDetail !== undefined && String(directDetail).trim()) {
    if (typeof directDetail === "string" && directDetail.trim().startsWith("{")) {
      try {
        const parsed = JSON.parse(directDetail);
        if (parsed.email && action.includes("login")) {
          return ip ? `Signed in from ${ip}` : "Signed in";
        }
      } catch {}
    } else {
      return valueText(directDetail);
    }
  }

  const ignoredKeys = new Set([
    "email", "actor_email", "user_email", "ip", "ip_address", "remote_addr",
    "client_ip", "request_ip", "before", "after"
  ]);
  const entries = Object.entries(data).filter(
    ([key, value]) =>
      !ignoredKeys.has(key) &&
      !["detail", "description", "message"].includes(key) &&
      value !== null && value !== ""
  );
  if (entries.length) {
    return entries.map(([key, value]) => {
      const readableKey = key.replaceAll("_", " ");
      const readableValue = typeof value === "object" ? JSON.stringify(value) : String(value);
      return `${readableKey}: ${readableValue}`;
    }).join(" · ");
  }
  return "";
}

function normalizeLog(log, index) {

  const action =

    log.action || log.event_type || log.event || log.action_type || "unknown";



  return {

    id: log.id ?? log.uuid ?? `${log.created_at || log.timestamp || "log"}-${index}`,

    timestamp:

      log.created_at ||

      log.timestamp ||

      log.created ||

      log.updated_at ||

      "",

    actor: getActor(log),

    action: String(action).replaceAll("_", "."),

    detail: getDetail(log),

  };

}



function formatTimestamp(value) {

  if (!value) return "—";



  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);



  const pad = (number) => String(number).padStart(2, "0");

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(

    date.getDate()

  )} ${pad(date.getHours())}:${pad(date.getMinutes())}`;

}



function actionClass(action) {

  const value = action.toLowerCase();



  if (value.includes("login") || value.includes("logout") || value.includes("auth") || value.includes("register")) return "auth";

  if (value.includes("role") || value.includes("permission")) return "role";

  if (value.includes("user") || value.includes("register")) return "user";

  return "other";

}



function extractLogs(payload) {

  if (Array.isArray(payload)) return payload;

  if (Array.isArray(payload?.results)) return payload.results;

  if (Array.isArray(payload?.audit_logs)) return payload.audit_logs;

  if (Array.isArray(payload?.logs)) return payload.logs;

  if (Array.isArray(payload?.data)) return payload.data;

  return [];

}



export default function AuditLog() {

  const [logs, setLogs] = useState([]);

  const [filter, setFilter] = useState("all");

  const [page, setPage] = useState(1);
  const [sortDirection, setSortDirection] = useState("desc");

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");



  useEffect(() => {

    let cancelled = false;



    async function loadLogs() {

      setLoading(true);

      setError("");



      try {

        const response = await apiClient.get("/audit-logs/");

        const items = extractLogs(response.data);

        const normalized = items

          .map(normalizeLog)

          .sort((a, b) => {

            const aTime = new Date(a.timestamp || 0).getTime();

            const bTime = new Date(b.timestamp || 0).getTime();

            return bTime - aTime;

          });



        if (!cancelled) setLogs(normalized);

      } catch (err) {

        const responseData = err.response?.data;

        const serverMessage =

          typeof responseData === "string"

            ? responseData.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim()

            : responseData?.detail ||

              responseData?.message ||

              responseData?.error;



        if (!cancelled) {

          setError(

            serverMessage ||

              err.message ||

              "Unable to load audit logs. Check that the backend is running and you are signed in."

          );

        }

      } finally {

        if (!cancelled) setLoading(false);

      }

    }



    loadLogs();

    return () => {

      cancelled = true;

    };

  }, []);



  const filteredLogs = useMemo(() => {
    const matchingLogs =
      filter === "all"
        ? logs
        : logs.filter((log) => actionClass(log.action) === filter);

    return [...matchingLogs].sort((a, b) => {
      const aTime = new Date(a.timestamp || 0).getTime();
      const bTime = new Date(b.timestamp || 0).getTime();
      return sortDirection === "desc" ? bTime - aTime : aTime - bTime;
    });
  }, [filter, logs, sortDirection]);

  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / PAGE_SIZE));

  const safePage = Math.min(page, totalPages);

  const visibleLogs = filteredLogs.slice(

    (safePage - 1) * PAGE_SIZE,

    safePage * PAGE_SIZE

  );



  const firstItem = filteredLogs.length ? (safePage - 1) * PAGE_SIZE + 1 : 0;

  const lastItem = Math.min(safePage * PAGE_SIZE, filteredLogs.length);



  function exportCsv() {

    const rows = [

      ["Timestamp", "Actor", "Action", "Detail"],

      ...filteredLogs.map((log) => [

        formatTimestamp(log.timestamp),

        log.actor,

        log.action,

        log.detail,

      ]),

    ];



    const csv = rows

      .map((row) =>

        row

          .map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`)

          .join(",")

      )

      .join("\r\n");



    const blob = new Blob(["\uFEFF", csv], {

      type: "text/csv;charset=utf-8;",

    });

    const url = URL.createObjectURL(blob);

    const anchor = document.createElement("a");

    anchor.href = url;

    anchor.download = "sentra-audit-log.csv";

    document.body.appendChild(anchor);

    anchor.click();

    anchor.remove();

    URL.revokeObjectURL(url);

  }



  return (

    <div className="sentra-audit-shell">

      <Sidebar />



      <main className="sentra-audit-main">

        <style>{`

          .sentra-audit-shell {

            display: flex;

            min-height: 100vh;

            background: #f5f7fa;

            color: #132033;

            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

          }

          .sentra-audit-main {

            box-sizing: border-box;

            flex: 1;

            min-width: 0;

            margin-left: 240px;

            width: calc(100% - 240px);

            padding: 30px 40px;

            background: #f5f7fa;

          }

          .sentra-audit-header {

            display: flex;

            align-items: flex-start;

            justify-content: space-between;

            gap: 20px;

            margin-bottom: 24px;

          }

          .sentra-audit-title {

            margin: 0 0 5px;

            color: #101b2c;

            font-size: 27px;

            line-height: 1.25;

            font-weight: 650;

            letter-spacing: -.45px;

          }

          .sentra-audit-subtitle {

            margin: 0;

            color: #61738d;

            font-size: 15px;

          }

          .sentra-audit-controls {

            display: flex;

            align-items: center;

            gap: 10px;

          }
          .sentra-audit-select,

          .sentra-audit-export {

            box-sizing: border-box;

            height: 44px;

            border: 1px solid #d5dde7;

            border-radius: 10px;

            background: #fff;

            color: #31415a;

            font-size: 14px;

          }

          .sentra-audit-select {

            min-width: 170px;

            max-width: 240px;

            padding: 0 36px 0 14px;

            cursor: pointer;

          }

          .sentra-audit-export {

            display: inline-flex;

            align-items: center;

            justify-content: center;

            gap: 10px;

            padding: 0 16px;

            font-weight: 600;

            cursor: pointer;

            white-space: nowrap;

          }

          .sentra-audit-export:hover,

          .sentra-audit-select:hover {

            border-color: #aab8c9;

          }

          .sentra-audit-card {

            overflow: hidden;

            border: 1px solid #e0e6ee;

            border-radius: 12px;

            background: #fff;

          }

          .sentra-audit-table-wrap {

            width: 100%;

            overflow-x: auto;

          }

          .sentra-audit-table {

            width: 100%;

            border-collapse: collapse;

            min-width: 760px;

          }

          .sentra-audit-table thead th {

            height: 40px;

            padding: 0 22px;

            border-bottom: 1px solid #e0e6ee;

            color: #8291a7;

            text-transform: uppercase;

            letter-spacing: .65px;

            font-size: 11px;

            font-weight: 750;

            text-align: left;

            white-space: nowrap;

          }

          .sentra-audit-sort {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 0;
            border: 0;
            background: transparent;
            color: inherit;
            font: inherit;
            letter-spacing: inherit;
            text-transform: inherit;
            cursor: pointer;
          }
          .sentra-audit-sort:hover { color: #263750; }

          .sentra-audit-table tbody td {

            height: 45px;

            padding: 0 22px;

            border-bottom: 1px solid #edf0f4;

            color: #41536d;

            font-size: 14px;

            white-space: nowrap;

          }

          .sentra-audit-table tbody tr:last-child td { border-bottom: 0; }

          .sentra-audit-table tbody tr:hover { background: #fafbfd; }

          .sentra-audit-time {

            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;

            font-size: 12px !important;

            color: #8190a7 !important;

          }

          .sentra-audit-actor {

            font-weight: 650;

            color: #111c2d !important;

          }

          .sentra-audit-badge {

            display: inline-flex;

            align-items: center;

            min-height: 22px;

            padding: 0 9px;

            border-radius: 999px;

            font-size: 12px;

            font-weight: 650;

            letter-spacing: -.1px;

          }

          .sentra-audit-badge.auth { background: #eef2ff; color: #4667dc; }

          .sentra-audit-badge.role { background: #f5edfb; color: #8a43bb; }

          .sentra-audit-badge.user { background: #eaf5f4; color: #087e83; }

          .sentra-audit-badge.other { background: #eef1f5; color: #58677d; }

          .sentra-audit-detail {

            max-width: 360px;

            overflow: hidden;

            text-overflow: ellipsis;

          }

          .sentra-audit-footer {

            min-height: 62px;

            box-sizing: border-box;

            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 16px;

            padding: 0 22px;

            background: #fafbfd;

            border-top: 1px solid #edf0f4;

            color: #60728b;

            font-size: 13px;

          }

          .sentra-audit-meta {

            display: flex;

            align-items: center;

            gap: 14px;

            flex-wrap: wrap;

          }

          .sentra-audit-muted {

            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;

            font-size: 12px;

            color: #9aa7b8;

          }

          .sentra-audit-pagination {

            display: flex;

            align-items: center;

            gap: 14px;

          }

          .sentra-audit-pagebtn {

            height: 35px;

            padding: 0 13px;

            border: 1px solid #d7dfe9;

            border-radius: 8px;

            background: #fff;

            color: #263750;

            font-size: 13px;

            font-weight: 600;

            cursor: pointer;

          }

          .sentra-audit-pagebtn:disabled {

            color: #b9c3d1;

            cursor: not-allowed;

          }

          .sentra-audit-pagecount {

            font-weight: 650;

            color: #142035;

            white-space: nowrap;

          }

          .sentra-audit-message {

            padding: 36px 22px !important;

            color: #61738d !important;

            font-size: 14px !important;

            white-space: normal !important;

          }

          .sentra-audit-error { color: #a63838 !important; }

          @media (max-width: 900px) {

            .sentra-audit-main {

              margin-left: 240px;

              width: calc(100% - 240px);

              padding: 24px;

            }

            .sentra-audit-header { flex-direction: column; }

            .sentra-audit-controls { width: 100%; flex-wrap: wrap; }

            .sentra-audit-footer {

              padding: 14px 18px;

              align-items: flex-start;

              flex-direction: column;

            }

            .sentra-audit-table thead th,

            .sentra-audit-table tbody td {

              padding-left: 16px;

              padding-right: 16px;

            }

          }

          @media (max-width: 560px) {

            .sentra-audit-main {

              margin-left: 0;

              width: 100%;

              padding: 20px 14px;

            }

            .sentra-audit-title { font-size: 24px; }

            .sentra-audit-controls { align-items: stretch; }

            .sentra-audit-export { flex: 1; }

          }

        `}</style>



        <header className="sentra-audit-header">

          <div>

            <h1 className="sentra-audit-title">Audit Log</h1>

            <p className="sentra-audit-subtitle">

              Append-only record of every sensitive action

            </p>

          </div>



          <div className="sentra-audit-controls">
            <select
              className="sentra-audit-select"
              value={filter}
              onChange={(event) => {
                setFilter(event.target.value);
                setPage(1);
              }}
              aria-label="Filter audit logs by category"
            >
              <option value="all">All actions</option>
              <option value="auth">Auth</option>
              <option value="user">User changes</option>
              <option value="role">Role changes</option>
            </select>

            <button className="sentra-audit-export" onClick={exportCsv}>

              <svg

                width="17"

                height="17"

                viewBox="0 0 24 24"

                fill="none"

                aria-hidden="true"

              >

                <path

                  d="M12 3v11m0 0 4-4m-4 4-4-4M5 17v3h14v-3"

                  stroke="currentColor"

                  strokeWidth="1.8"

                  strokeLinecap="round"

                  strokeLinejoin="round"

                />

              </svg>

              Export to Excel

            </button>

          </div>

        </header>



        <section className="sentra-audit-card" aria-label="Audit log records">

          <div className="sentra-audit-table-wrap">

            <table className="sentra-audit-table">

              <thead>

                <tr>

                  <th>
                    <button
                      type="button"
                      className="sentra-audit-sort"
                      onClick={() => {
                        setSortDirection((current) => current === "desc" ? "asc" : "desc");
                        setPage(1);
                      }}
                      aria-label="Sort audit logs by timestamp"
                      title="Click to sort oldest/newest"
                    >
                      Timestamp {sortDirection === "desc" ? "↓" : "↑"}
                    </button>
                  </th>

                  <th>Actor</th>

                  <th>Action</th>

                  <th>Detail</th>

                </tr>

              </thead>

              <tbody>

                {loading ? (

                  <tr>

                    <td colSpan="4" className="sentra-audit-message">

                      Loading audit logs…

                    </td>

                  </tr>

                ) : error ? (

                  <tr>

                    <td

                      colSpan="4"

                      className="sentra-audit-message sentra-audit-error"

                    >

                      {error}

                    </td>

                  </tr>

                ) : visibleLogs.length === 0 ? (

                  <tr>

                    <td colSpan="4" className="sentra-audit-message">

                      No audit log records found.

                    </td>

                  </tr>

                ) : (

                  visibleLogs.map((log) => (

                    <tr key={log.id}>

                      <td className="sentra-audit-time">

                        {formatTimestamp(log.timestamp)}

                      </td>

                      <td className="sentra-audit-actor">{log.actor}</td>

                      <td>

                        <span

                          className={`sentra-audit-badge ${actionClass(log.action)}`}

                        >

                          {log.action}

                        </span>

                      </td>

                      <td className="sentra-audit-detail" title={log.detail || "—"}>

                        {log.detail || "—"}

                      </td>

                    </tr>

                  ))

                )}

              </tbody>

            </table>

          </div>



          <footer className="sentra-audit-footer">

            <div className="sentra-audit-meta">

              <span>

                Showing {firstItem}–{lastItem} of {filteredLogs.length}

              </span>

              <span className="sentra-audit-muted">

                client-side · page_size={PAGE_SIZE}

              </span>

            </div>



            <div className="sentra-audit-pagination">

              <button

                className="sentra-audit-pagebtn"

                disabled={safePage <= 1}

                onClick={() => setPage((current) => Math.max(1, current - 1))}

              >

                ← Prev

              </button>

              <span className="sentra-audit-pagecount">

                {safePage} / {totalPages}

              </span>

              <button

                className="sentra-audit-pagebtn"

                disabled={safePage >= totalPages}

                onClick={() =>

                  setPage((current) => Math.min(totalPages, current + 1))

                }

              >

                Next →

              </button>

            </div>

          </footer>

        </section>

      </main>

    </div>

  );

}
