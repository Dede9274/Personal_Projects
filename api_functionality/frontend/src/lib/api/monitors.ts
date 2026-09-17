import { apiRequest } from "@/lib/api/client";
import type {
  CheckResult,
  CreateMonitorInput,
  ManualCheckQueueResponse,
  Monitor,
  UpdateMonitorInput,
} from "@/lib/api/types";

export function getMonitors(): Promise<Monitor[]> {
  return apiRequest<Monitor[]>("/monitors", {
    cache: "no-store",
  });
}

export function getMonitor(monitorId: number): Promise<Monitor> {
  return apiRequest<Monitor>(`/monitors/${monitorId}`, {
    cache: "no-store",
  });
}

export function createMonitor(data: CreateMonitorInput): Promise<Monitor> {
  return apiRequest<Monitor>("/monitors", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
}

export function updateMonitor(
  monitorId: number,
  changes: UpdateMonitorInput,
): Promise<Monitor> {
  return apiRequest<Monitor>(`/monitors/${monitorId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(changes),
  });
}

export function deleteMonitor(monitorId: number): Promise<void> {
  return apiRequest<void>(`/monitors/${monitorId}`, {
    method: "DELETE",
  });
}

export function runMonitorCheck(
  monitorId: number,
): Promise<ManualCheckQueueResponse> {
  return apiRequest<ManualCheckQueueResponse>(`/monitors/${monitorId}/checks`, {
    method: "POST",
  });
}

type GetMonitorChecksOptions = {
  limit?: number;
  signal?: AbortSignal;
};

export function getMonitorChecks(
  monitorId: number,
  { limit = 500, signal }: GetMonitorChecksOptions = {},
): Promise<CheckResult[]> {
  const query = new URLSearchParams({ limit: String(limit) });

  return apiRequest<CheckResult[]>(
    `/monitors/${monitorId}/checks?${query.toString()}`,
    {
      cache: "no-store",
      signal,
    },
  );
}
