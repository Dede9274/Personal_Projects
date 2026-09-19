import DashboardAutoRefresh from "@/components/dashboard/DashboardAutoRefresh";
import MonitorStatusChart from "@/components/dashboard/MonitorStatusChart";
import MonitorTable from "@/components/dashboard/MonitorTable";
import type { DashboardMonitorRow } from "@/components/dashboard/MonitorTable";
import RecentIncidents from "@/components/dashboard/RecentIncidents";
import type { IncidentNotification } from "@/components/dashboard/RecentIncidents";
import ResponseTimeChart from "@/components/dashboard/ResponseTimeChart";
import type { ResponseTimePoint } from "@/components/dashboard/ResponseTimeChart";
import { getIncidents } from "@/lib/api/incidents";
import { getMonitorChecks, getMonitors } from "@/lib/api/monitors";
import { formatBerlinChartTime } from "@/lib/dateTime";
import type { CheckResult, Incident, Monitor } from "@/lib/api/types";
import { getMonitorHealth } from "@/lib/monitorHealth";

export const dynamic = "force-dynamic";

const DASHBOARD_CHECK_LIMIT = 100;
const RESPONSE_TIME_BUCKET_MS = 5 * 60 * 1_000;
const MAX_RESPONSE_TIME_POINTS = 48;

const berlinDateFormatter = new Intl.DateTimeFormat("en-GB", {
  weekday: "long",
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "Europe/Berlin",
});

const berlinTimeFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "Europe/Berlin",
  timeZoneName: "short",
});

const berlinHourFormatter = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  hourCycle: "h23",
  timeZone: "Europe/Berlin",
});

function getGreeting(now: Date): string {
  const hour = Number(berlinHourFormatter.format(now));

  if (hour < 12) return "Good morning!";
  if (hour < 18) return "Good afternoon!";
  return "Good evening!";
}

function buildResponseTimeData(
  rows: DashboardMonitorRow[],
  checksByMonitor: Map<number, CheckResult[]>,
): ResponseTimePoint[] {
  const buckets = new Map<number, { total: number; count: number }>();

  for (const row of rows) {
    if (!row.monitor.is_active) continue;

    for (const check of checksByMonitor.get(row.monitor.id) ?? []) {
      if (!check.success) continue;

      const checkedAt = Date.parse(check.checked_at);
      if (Number.isNaN(checkedAt)) continue;

      const bucket =
        Math.floor(checkedAt / RESPONSE_TIME_BUCKET_MS) *
        RESPONSE_TIME_BUCKET_MS;
      const current = buckets.get(bucket) ?? { total: 0, count: 0 };
      current.total += check.latency_ms;
      current.count += 1;
      buckets.set(bucket, current);
    }
  }

  return [...buckets.entries()]
    .sort(([left], [right]) => left - right)
    .slice(-MAX_RESPONSE_TIME_POINTS)
    .map(([timestamp, bucket]) => ({
      time: formatBerlinChartTime(timestamp),
      responseTime: Number((bucket.total / bucket.count).toFixed(2)),
    }));
}

function formatRelativeTime(value: string, now: number): string {
  const elapsedSeconds = Math.max(
    0,
    Math.floor((now - Date.parse(value)) / 1_000),
  );

  if (elapsedSeconds < 10) return "just now";
  if (elapsedSeconds < 60) return `${elapsedSeconds}s ago`;

  const minutes = Math.floor(elapsedSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function buildIncidentNotifications(
  incidents: Incident[],
  monitors: Monitor[],
  now: number,
): IncidentNotification[] {
  const monitorNames = new Map(
    monitors.map((monitor) => [monitor.id, monitor.name]),
  );

  return [...incidents]
    .sort((left, right) => {
      const leftTime = Date.parse(left.resolved_at ?? left.started_at);
      const rightTime = Date.parse(right.resolved_at ?? right.started_at);
      return rightTime - leftTime || right.id - left.id;
    })
    .slice(0, 5)
    .map((incident) => {
      const monitorName =
        monitorNames.get(incident.monitor_id) ??
        `Monitor ${incident.monitor_id}`;
      const isResolved = incident.status === "RESOLVED";
      const occurredAtIso = incident.resolved_at ?? incident.started_at;

      return {
        id: incident.id,
        title: isResolved
          ? `${monitorName} recovered`
          : incident.status === "INVESTIGATING"
            ? `${monitorName} incident under investigation`
            : `${monitorName} incident opened`,
        message:
          incident.last_error ??
          (isResolved ? "Incident resolved" : "Consecutive checks failed"),
        occurredAt: formatRelativeTime(occurredAtIso, now),
        occurredAtIso,
        severity: isResolved ? "resolved" : "critical",
      };
    });
}

function percentage(value: number, total: number): number {
  return total === 0 ? 0 : Math.round((value / total) * 100);
}

export default async function Home() {
  const nowDate = new Date();
  const now = nowDate.getTime();
  const [monitorsResult, incidentsResult] = await Promise.allSettled([
    getMonitors(),
    getIncidents(),
  ]);

  const monitors =
    monitorsResult.status === "fulfilled" ? monitorsResult.value : [];
  const incidents =
    incidentsResult.status === "fulfilled" ? incidentsResult.value : [];
  const monitorLoadError =
    monitorsResult.status === "rejected"
      ? monitorsResult.reason instanceof Error
        ? monitorsResult.reason.message
        : "The monitor API could not be reached."
      : null;
  const incidentLoadError =
    incidentsResult.status === "rejected"
      ? incidentsResult.reason instanceof Error
        ? incidentsResult.reason.message
        : "The incident API could not be reached."
      : null;

  const checkResults = await Promise.allSettled(
    monitors.map((monitor) =>
      getMonitorChecks(monitor.id, { limit: DASHBOARD_CHECK_LIMIT }),
    ),
  );
  const checksByMonitor = new Map<number, CheckResult[]>();
  let failedCheckHistories = 0;

  checkResults.forEach((result, index) => {
    const monitor = monitors[index];

    if (result.status === "fulfilled") {
      checksByMonitor.set(monitor.id, result.value);
    } else {
      failedCheckHistories += 1;
    }
  });

  const monitorRows: DashboardMonitorRow[] = monitors.map((monitor, index) => {
    const checksLoaded = checkResults[index]?.status === "fulfilled";
    const checks = checksByMonitor.get(monitor.id) ?? [];
    const latestCheck = checks[0] ?? null;

    return {
      monitor,
      latestCheck,
      health: getMonitorHealth(
        monitor,
        latestCheck,
        checksLoaded,
        now,
      ),
    };
  });

  const upCount = monitorRows.filter((row) => row.health === "up").length;
  const downCount = monitorRows.filter((row) => row.health === "down").length;
  const pausedCount = monitorRows.filter(
    (row) => row.health === "paused",
  ).length;
  const pendingCount = monitorRows.filter((row) =>
    ["awaiting", "delayed", "unavailable"].includes(row.health),
  ).length;
  const activeCount = monitors.length - pausedCount;
  const activeIncidentCount = incidents.filter(
    (incident) => incident.status !== "RESOLVED",
  ).length;
  const upPercentage = percentage(upCount, activeCount);
  const downPercentage = percentage(downCount, activeCount);
  const responseTimeData = buildResponseTimeData(
    monitorRows,
    checksByMonitor,
  );
  const recentIncidents = buildIncidentNotifications(
    incidents,
    monitors,
    now,
  );

  return (
    <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <DashboardAutoRefresh />

      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
            {getGreeting(nowDate)}
          </h1>
          <p className="mt-1 text-base text-slate-500">
            Here&apos;s the current state of your API monitors.
          </p>
        </div>
        <time
          dateTime={nowDate.toISOString()}
          className="text-left text-sm capitalize leading-6 text-slate-500 sm:text-right"
        >
          {berlinDateFormatter.format(nowDate)}
          <br />
          {berlinTimeFormatter.format(nowDate)}
        </time>
      </header>

      {monitorLoadError && (
        <section
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700"
        >
          Monitor data could not be loaded. {monitorLoadError}
        </section>
      )}

      {!monitorLoadError && failedCheckHistories > 0 && (
        <section
          role="alert"
          className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800"
        >
          Current check data is unavailable for {failedCheckHistories}{" "}
          {failedCheckHistories === 1 ? "monitor" : "monitors"}. Their status
          is shown as unavailable.
        </section>
      )}

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Total Monitors</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">
            {monitors.length}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {activeCount} active · {pausedCount} paused
          </p>
        </article>

        <article className="rounded-xl border border-emerald-100 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Monitors Up</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{upCount}</p>
          <p className="mt-1 text-xs text-slate-500">
            {upPercentage}% of active monitors
          </p>
          <div className="mt-3 h-1.5 rounded-full bg-emerald-100">
            <div
              className="h-1.5 rounded-full bg-emerald-500"
              style={{ width: `${upPercentage}%` }}
            />
          </div>
        </article>

        <article className="rounded-xl border border-red-100 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Monitors Down</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{downCount}</p>
          <p className="mt-1 text-xs text-slate-500">
            {downPercentage}% of active monitors
          </p>
          <div className="mt-3 h-1.5 rounded-full bg-red-100">
            <div
              className="h-1.5 rounded-full bg-red-500"
              style={{ width: `${downPercentage}%` }}
            />
          </div>
        </article>

        <article
          className={`rounded-xl border bg-white p-5 shadow-sm ${
            activeIncidentCount > 0 ? "border-red-100" : "border-blue-100"
          }`}
        >
          <p className="text-[15px] font-semibold text-slate-500">
            Active Incidents
          </p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">
            {incidentLoadError ? "—" : activeIncidentCount}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {incidentLoadError
              ? "Incident data unavailable"
              : `${incidents.length} total recorded`}
          </p>
        </article>
      </section>

      <section
        className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]"
        aria-label="Monitoring overview"
      >
        <ResponseTimeChart data={responseTimeData} />
        <MonitorStatusChart
          up={upCount}
          down={downCount}
          paused={pausedCount}
          pending={pendingCount}
        />
      </section>

      <section
        className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]"
        aria-label="Latest monitoring activity"
      >
        <MonitorTable rows={monitorRows} />
        <RecentIncidents
          incidents={recentIncidents}
          loadError={incidentLoadError}
        />
      </section>
    </main>
  );
}
