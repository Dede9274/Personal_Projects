import type { CheckResult, Incident, Monitor } from "@/lib/api/types";

export const LATENCY_WARNING_THRESHOLD_MS = 1_500;
export const LATENCY_WARNING_DURATION_MS = 10 * 60 * 1_000;
export const CRITICAL_OUTAGE_THRESHOLD_MS = 10 * 60 * 1_000;

export type IncidentSeverity = "critical" | "high" | "medium" | "low";
export type IncidentActivityStatus =
  | "open"
  | "investigating"
  | "resolved";
export type IncidentActivitySource = "outage" | "latency";

export type IncidentActivity = {
  key: string;
  incidentId: number | null;
  monitorId: number;
  title: string;
  error: string;
  monitorName: string;
  monitorUrl: string;
  severity: IncidentSeverity;
  status: IncidentActivityStatus;
  startedAt: string;
  endedAt: string | null;
  durationMs: number;
  source: IncidentActivitySource;
};

function timestamp(value: string | null): number | null {
  if (value === null) return null;

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function elapsedMilliseconds(
  startedAt: string,
  endedAt: string | null,
  now: number,
): number {
  const start = timestamp(startedAt);
  const end = timestamp(endedAt) ?? now;

  if (start === null || end < start) return 0;
  return end - start;
}

export function getOutageSeverity(
  incident: Incident,
  now: number,
): IncidentSeverity {
  if (incident.status === "RESOLVED") return "low";

  const startedAt = timestamp(incident.started_at);
  if (
    startedAt !== null &&
    now - startedAt > CRITICAL_OUTAGE_THRESHOLD_MS
  ) {
    return "critical";
  }

  return "high";
}

function monitorDetails(
  monitorId: number,
  monitorsById: Map<number, Monitor>,
): { name: string; url: string } {
  const monitor = monitorsById.get(monitorId);

  return {
    name: monitor?.name ?? `Monitor ${monitorId}`,
    url: monitor?.url ?? "Monitor details unavailable",
  };
}

function buildOutageActivities(
  incidents: Incident[],
  monitorsById: Map<number, Monitor>,
  now: number,
): IncidentActivity[] {
  return incidents.map((incident) => {
    const monitor = monitorDetails(incident.monitor_id, monitorsById);
    const isResolved = incident.status === "RESOLVED";

    return {
      key: `incident-${incident.id}`,
      incidentId: incident.id,
      monitorId: incident.monitor_id,
      title: isResolved
        ? `${monitor.name} recovered`
        : `${monitor.name} is down`,
      error:
        incident.last_error ??
        (isResolved
          ? "The monitor is responding normally again."
          : "The monitor failed consecutive checks."),
      monitorName: monitor.name,
      monitorUrl: monitor.url,
      severity: getOutageSeverity(incident, now),
      status: incident.status.toLowerCase() as IncidentActivityStatus,
      startedAt: incident.started_at,
      endedAt: incident.resolved_at,
      durationMs: elapsedMilliseconds(
        incident.started_at,
        incident.resolved_at,
        now,
      ),
      source: "outage",
    };
  });
}

export type SustainedLatencyEpisode = {
  firstCheckId: number;
  startedAt: string;
  alertAt: string;
  lastSlowAt: string;
  endedAt: string | null;
  peakLatencyMs: number;
};

type PendingLatencyEpisode = Omit<
  SustainedLatencyEpisode,
  "alertAt" | "endedAt"
>;

export function getSustainedLatencyEpisodes(
  checks: CheckResult[],
  latencyThresholdMs = LATENCY_WARNING_THRESHOLD_MS,
  minimumDurationMs = LATENCY_WARNING_DURATION_MS,
): SustainedLatencyEpisode[] {
  const chronologicalChecks = [...checks]
    .filter((check) => timestamp(check.checked_at) !== null)
    .sort(
      (left, right) =>
        Date.parse(left.checked_at) - Date.parse(right.checked_at) ||
        left.id - right.id,
    );
  const episodes: SustainedLatencyEpisode[] = [];
  let pendingEpisode: PendingLatencyEpisode | null = null;

  const finishEpisode = (endedAt: string | null) => {
    const episode = pendingEpisode;
    pendingEpisode = null;

    if (episode === null) return;

    const startedAt = timestamp(episode.startedAt);
    const lastSlowAt = timestamp(episode.lastSlowAt);
    if (
      startedAt === null ||
      lastSlowAt === null ||
      lastSlowAt - startedAt < minimumDurationMs
    ) {
      return;
    }

    episodes.push({
      ...episode,
      alertAt: new Date(startedAt + minimumDurationMs).toISOString(),
      endedAt,
    });
  };

  for (const check of chronologicalChecks) {
    const isAboveThreshold =
      check.success && check.latency_ms > latencyThresholdMs;

    if (!isAboveThreshold) {
      finishEpisode(check.checked_at);
      continue;
    }

    if (pendingEpisode === null) {
      pendingEpisode = {
        firstCheckId: check.id,
        startedAt: check.checked_at,
        lastSlowAt: check.checked_at,
        peakLatencyMs: check.latency_ms,
      };
      continue;
    }

    pendingEpisode.lastSlowAt = check.checked_at;
    pendingEpisode.peakLatencyMs = Math.max(
      pendingEpisode.peakLatencyMs,
      check.latency_ms,
    );
  }

  finishEpisode(null);
  return episodes;
}

function buildLatencyActivities(
  monitor: Monitor,
  checks: CheckResult[],
  now: number,
  latencyThresholdMs: number,
): IncidentActivity[] {
  return getSustainedLatencyEpisodes(checks, latencyThresholdMs).map(
    (episode) => ({
      key: `latency-${monitor.id}-${episode.firstCheckId}`,
      incidentId: null,
      monitorId: monitor.id,
      title: `${monitor.name} latency high for 10+ minutes`,
      error: `Response time stayed above ${latencyThresholdMs.toLocaleString(
        "en-GB",
      )} ms for at least 10 minutes and peaked at ${Math.round(
        episode.peakLatencyMs,
      ).toLocaleString("en-GB")} ms.`,
      monitorName: monitor.name,
      monitorUrl: monitor.url,
      severity: "medium",
      status: episode.endedAt === null ? "open" : "resolved",
      startedAt: episode.startedAt,
      endedAt: episode.endedAt,
      durationMs: elapsedMilliseconds(
        episode.startedAt,
        episode.endedAt,
        now,
      ),
      source: "latency",
    }),
  );
}

export function buildIncidentActivities({
  incidents,
  monitors,
  checksByMonitor,
  now,
  latencyThresholdMs = LATENCY_WARNING_THRESHOLD_MS,
}: {
  incidents: Incident[];
  monitors: Monitor[];
  checksByMonitor: Map<number, CheckResult[]>;
  now: number;
  latencyThresholdMs?: number;
}): IncidentActivity[] {
  const monitorsById = new Map(
    monitors.map((monitor) => [monitor.id, monitor]),
  );
  const outageActivities = buildOutageActivities(
    incidents,
    monitorsById,
    now,
  );
  const latencyActivities = monitors.flatMap((monitor) =>
    buildLatencyActivities(
      monitor,
      checksByMonitor.get(monitor.id) ?? [],
      now,
      latencyThresholdMs,
    ),
  );

  return [...outageActivities, ...latencyActivities].sort((left, right) => {
    const leftTime = timestamp(left.startedAt) ?? 0;
    const rightTime = timestamp(right.startedAt) ?? 0;
    return rightTime - leftTime || right.key.localeCompare(left.key);
  });
}
