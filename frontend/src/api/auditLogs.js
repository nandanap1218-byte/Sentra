import apiClient from "./apiClient";

export const getAuditLogs = async () => {
  const response = await apiClient.get("/audit-logs/");
  return response.data;
};

export const getAuditLog = async (auditLogId) => {
  const response = await apiClient.get(`/audit-logs/${auditLogId}/`);
  return response.data;
};