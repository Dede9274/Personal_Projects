import DashboardAutoRefresh from "@/components/dashboard/DashboardAutoRefresh";
import IncidentSearchBar from "@/components/incidents/IncidentSearchBar";
import IncidentTable from "@/components/incidents/IncidentTable";
import { getIncidents } from "@/lib/api/incidents";
import { getMonitorChecks, getMonitors } from "@/lib/api/monitors";
import type { CheckResult, Incident, Monitor } from "@/lib/api/types";
import {
  buildIncidentActivities,
  type IncidentActivity,
  type IncidentSeverity,
  LATENCY_WARNING_THRESHOLD_MS,
} from "@/lib/incidentActivity";

export const dynamic = "force-dynamic";

const CHECK_HISTORY_LIMIT = 500;
const DAY_MS = 24 * 60 * 60 * 1_000;

type IncidentsPageProps = {
  searchParams: Promise<{
    query?: string;
    status?: string;
    severity?: string;
    range?: string;
    sort?: string;
  }>;
};

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

const berlinDayFormatter = new Intl.DateTimeFormat("en-GB", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  timeZone: "Europe/Berlin",
});

const severityRank: Record<IncidentSeverity, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

function validFilter(value: string | undefined, allowed: string[], fallback: string) {
  return value !== undefined && allowed.includes(value) ? value : fallback;
}

function berlinDayKey(value: string | number | Date): string | null {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  const parts = berlinDayFormatter.formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;

  return year && month && day ? `${year}-${month}-${day}` : null;
}

function resolutionDuration(incident: Incident): number | null {
  if (incident.status !== "RESOLVED" || incident.resolved_at === null) {
    return null;
  }

  const startedAt = Date.parse(incident.started_at);
  const resolvedAt = Date.parse(incident.resolved_at);
  if (
    Number.isNaN(startedAt) ||
    Number.isNaN(resolvedAt) ||
    resolvedAt < startedAt
  ) {
    return null;
  }

  return resolvedAt - startedAt;
}

function formatAverageDuration(durationMs: number | null): string {
  if (durationMs === null) return "—";

  const minutes = Math.max(0, Math.round(durationMs / 60_000));
  if (minutes < 1) return "<1 min";
  if (minutes < 60) return `${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (hours < 24) {
    return remainingMinutes === 0
      ? `${hours} hr`
      : `${hours}h ${remainingMinutes}m`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours === 0
    ? `${days}d`
    : `${days}d ${remainingHours}h`;
}

function rangeCutoff(range: string, now: number): number | null {
  if (range === "24-hours") return now - DAY_MS;
  if (range === "7-days") return now - 7 * DAY_MS;
  if (range === "30-days") return now - 30 * DAY_MS;
  if (range === "90-days") return now - 90 * DAY_MS;
  return null;
}

function filterAndSortActivities(
  activities: IncidentActivity[],
  filters: {
    query: string;
    status: string;
    severity: string;
    range: string;
    sort: string;
  },
  now: number,
): IncidentActivity[] {
  const normalizedQuery = filters.query.trim().toLowerCase();
  const cutoff = rangeCutoff(filters.range, now);
  const filtered = activities.filter((activity) => {
    const searchableText = [
      activity.title,
      activity.error,
      activity.monitorName,
      activity.monitorUrl,
    ]
      .join(" ")
      .toLowerCase();
    const startedAt = Date.parse(activity.startedAt);

    return (
      (normalizedQuery.length === 0 || searchableText.includes(normalizedQuery)) &&
      (filters.status === "all" || activity.status === filters.status) &&
      (filters.severity === "all" || activity.severity === filters.severity) &&
      (cutoff === null || (!Number.isNaN(startedAt) && startedAt >= cutoff))
    );
  });

  return [...filtered].sort((left, right) => {
    const leftStartedAt = Date.parse(left.startedAt) || 0;
    const rightStartedAt = Date.parse(right.startedAt) || 0;

    if (filters.sort === "started-asc") {
      return leftStartedAt - rightStartedAt;
    }

    if (filters.sort === "severity") {
      return (
        severityRank[right.severity] - severityRank[left.severity] ||
        rightStartedAt - leftStartedAt
      );
    }

    if (filters.sort === "duration") {
      return right.durationMs - left.durationMs || rightStartedAt - leftStartedAt;
    }

    return rightStartedAt - leftStartedAt;
  });
}

function SummaryCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string | number;
  detail: string;
  tone: "red" | "green" | "blue" | "orange";
}) {
  const tones = {
    red: "border-red-100 bg-red-50/30",
    green: "border-emerald-100 bg-emerald-50/30",
    blue: "border-blue-100 bg-blue-50/30",
    orange: "border-orange-100 bg-orange-50/30",
  };

  return (
    <article className={`rounded-xl border p-5 shadow-sm ${tones[tone]}`}>
      <p className="text-[15px] font-semibold text-slate-500">{label}</p>
      <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </article>
  );
}

export default async function IncidentsPage({
  searchParams,
}: IncidentsPageProps) {
  const rawFilters = await searchParams;
  const filters = {
    query: rawFilters.query ?? "",
    status: validFilter(
      rawFilters.status,
      ["all", "open", "investigating", "resolved"],
      "all",
    ),
    severity: validFilter(
      rawFilters.severity,
      ["all", "critical", "high", "medium", "low"],
      "all",
    ),
    range: validFilter(
      rawFilters.range,
      ["24-hours", "7-days", "30-days", "90-days", "all"],
      "7-days",
    ),
    sort: validFilter(
      rawFilters.sort,
      ["started-desc", "started-asc", "severity", "duration"],
      "started-desc",
    ),
  };
  const nowDate = new Date();
  const now = nowDate.getTime();

  const [incidentsResult, monitorsResult] = await Promise.allSettled([
    getIncidents(),
    getMonitors(),
  ]);
  const incidents: Incident[] =
    incidentsResult.status === "fulfilled" ? incidentsResult.value : [];
  const monitors: Monitor[] =
    monitorsResult.status === "fulfilled" ? monitorsResult.value : [];
  const incidentLoadError =
    incidentsResult.status === "rejected"
      ? incidentsResult.reason instanceof Error
        ? incidentsResult.reason.message
        : "The incident API could not be reached."
      : null;
  const monitorLoadError =
    monitorsResult.status === "rejected"
      ? monitorsResult.reason instanceof Error
        ? monitorsResult.reason.message
        : "The monitor API could not be reached."
      : null;

  const checkResults = await Promise.allSettled(
    monitors.map((monitor) =>
      getMonitorChecks(monitor.id, { limit: CHECK_HISTORY_LIMIT }),
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

  const activities = buildIncidentActivities({
    incidents,
    monitors,
    checksByMonitor,
    now,
  });
  const visibleActivities = filterAndSortActivities(
    activities,
    filters,
    now,
  );
  const searchOptions = [
    ...new Set(
      activities.flatMap((activity) => [
        activity.title,
        activity.monitorName,
      ]),
    ),
  ].sort((left, right) => left.localeCompare(right));

  const openIncidents = incidents.filter(
    (incident) => incident.status !== "RESOLVED",
  );
  const openedLast24Hours = incidents.filter((incident) => {
    const startedAt = Date.parse(incident.started_at);
    return !Number.isNaN(startedAt) && startedAt >= now - DAY_MS;
  }).length;
  const todayKey = berlinDayKey(nowDate);
  const resolvedToday = incidents.filter(
    (incident) =>
      incident.status === "RESOLVED" &&
      incident.resolved_at !== null &&
      berlinDayKey(incident.resolved_at) === todayKey,
  ).length;
  const resolutionDurations = incidents
    .map(resolutionDuration)
    .filter((duration): duration is number => duration !== null);
  const averageResolutionMs =
    resolutionDurations.length === 0
      ? null
      : resolutionDurations.reduce((total, duration) => total + duration, 0) /
        resolutionDurations.length;
  const openOutageActivities = activities.filter(
    (activity) =>
      activity.source === "outage" && activity.status !== "resolved",
  );
  const criticalCount = openOutageActivities.filter(
    (activity) => activity.severity === "critical",
  ).length;
  const highCount = openOutageActivities.filter(
    (activity) => activity.severity === "high",
  ).length;
  const summariesUnavailable = incidentLoadError !== null;

  return (
    <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <DashboardAutoRefresh />

      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
            Incidents
          </h1>
          <p className="mt-1 text-base text-slate-500">
            Track outages, recoveries, and slow responses across your monitored APIs.
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

      {incidentLoadError && (
        <section
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700"
        >
          <p className="font-semibold">Incident history is unavailable</p>
          <p className="mt-1">{incidentLoadError}</p>
        </section>
      )}

      {monitorLoadError && (
        <section
          role="alert"
          className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800"
        >
          Monitor names and latency warnings could not be loaded: {monitorLoadError}
        </section>
      )}

      {failedCheckHistories > 0 && (
        <section
          role="status"
          className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800"
        >
          Latency history is temporarily unavailable for {failedCheckHistories}{" "}
          {failedCheckHistories === 1 ? "monitor" : "monitors"}.
        </section>
      )}

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Open Incidents"
          value={summariesUnavailable ? "—" : openIncidents.length}
          detail={
            summariesUnavailable
              ? "Waiting for incident data"
              : `${openedLast24Hours} opened in the last 24 hours`
          }
          tone="red"
        />
        <SummaryCard
          label="Resolved Today"
          value={summariesUnavailable ? "—" : resolvedToday}
          detail="Based on the Europe/Berlin calendar day"
          tone="green"
        />
        <SummaryCard
          label="Average Resolution Time"
          value={
            summariesUnavailable ? "—" : formatAverageDuration(averageResolutionMs)
          }
          detail={
            summariesUnavailable
              ? "Waiting for incident data"
              : `${resolutionDurations.length} resolved ${
                  resolutionDurations.length === 1 ? "incident" : "incidents"
                } measured`
          }
          tone="blue"
        />
        <SummaryCard
          label="High & Critical"
          value={summariesUnavailable ? "—" : highCount + criticalCount}
          detail={
            summariesUnavailable
              ? "Waiting for incident data"
              : `${criticalCount} critical · ${highCount} high`
          }
          tone="orange"
        />
      </section>

      <p className="mt-4 text-xs text-slate-500">
        Severity rules: recovered incidents are low, responses above{" "}
        {LATENCY_WARNING_THRESHOLD_MS.toLocaleString("en-GB")} ms across
        consecutive checks for at least 10 minutes are medium, active outages
        are high, and outages lasting more than 10 minutes are critical.
      </p>

      <IncidentSearchBar
        key={filters.query}
        query={filters.query}
        status={filters.status}
        severity={filters.severity}
        range={filters.range}
        sort={filters.sort}
        searchOptions={searchOptions}
      />
      <IncidentTable
        incidents={visibleActivities}
        totalCount={activities.length}
        now={now}
      />
    </main>
  );
}
