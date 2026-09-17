import { apiRequest } from "@/lib/api/client";
import type { Incident, IncidentStatus } from "@/lib/api/types";

type GetMonitorIncidentsOptions = {
  signal?: AbortSignal;
};

type GetIncidentsOptions = {
  signal?: AbortSignal;
};

export function getIncidents(
  { signal }: GetIncidentsOptions = {},
): Promise<Incident[]> {
  return apiRequest<Incident[]>("/incidents", {
    cache: "no-store",
    signal,
  });
}

export function getMonitorIncidents(
  monitorId: number,
  { signal }: GetMonitorIncidentsOptions = {},
): Promise<Incident[]> {
  return apiRequest<Incident[]>(`/monitors/${monitorId}/incidents`, {
    cache: "no-store",
    signal,
  });
}

export function updateIncidentStatus(
  incidentId: number,
  status: IncidentStatus,
): Promise<Incident> {
  return apiRequest<Incident>(`/incidents/${incidentId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
}
