import type { CheckResult, Monitor } from "@/lib/api/types";

export type MonitorHealth =
  | "up"
  | "down"
  | "blocked"
  | "paused"
  | "awaiting"
  | "delayed"
  | "unavailable";

export function getMonitorHealth(
  monitor: Monitor,
  latestCheck: CheckResult | null,
  checksLoaded: boolean,
  now: number,
): MonitorHealth {
  if (!monitor.is_active) return "paused";
  if (!checksLoaded) return "unavailable";
  if (latestCheck === null) return "awaiting";

  const checkedAt = Date.parse(latestCheck.checked_at);
  if (Number.isNaN(checkedAt)) return "unavailable";

  const expectedCheckWindowMs = Math.max(
    monitor.interval_seconds * 3 * 1_000,
    30_000,
  );

  if (now - checkedAt > expectedCheckWindowMs) return "delayed";
  if (latestCheck.security_rejected) return "blocked";
  return latestCheck.success ? "up" : "down";
}
