export type Monitor = {
  id: number;
  name: string;
  url: string;
  purpose: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_code: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CreateMonitorInput = {
  name: string;
  url: string;
  purpose: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_code: number;
  is_active: boolean;
};

export type UpdateMonitorInput = Partial<CreateMonitorInput>;

export type CheckResult = {
  id: number;
  monitor_id: number;
  checked_at: string;
  status_code: number | null;
  latency_ms: number;
  success: boolean;
  error: string | null;
};

export type ManualCheckQueueResponse = {
  monitor_id: number;
  status: "queued" | "already_outstanding";
  job_id: string | null;
};

export type IncidentStatus = "OPEN" | "INVESTIGATING" | "RESOLVED";

export type Incident = {
  id: number;
  monitor_id: number;
  status: IncidentStatus;
  started_at: string;
  resolved_at: string | null;
  failure_count: number;
  last_error: string | null;
  created_at: string;
};
