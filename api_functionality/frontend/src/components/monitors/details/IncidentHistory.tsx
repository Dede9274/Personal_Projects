import Link from "next/link";

import type { CheckResult, Incident } from "@/lib/api/types";
import {
  getSustainedLatencyEpisodes,
  LATENCY_WARNING_DURATION_MS,
  LATENCY_WARNING_THRESHOLD_MS,
} from "@/lib/incidentActivity";

const MAX_HISTORY_ITEMS = 4;

type HistoryTone = "critical" | "warning" | "resolved";

type HistoryItem = {
  key: string;
  occurredAt: number;
  title: string;
  description: string;
  metadata: string;
  label: string;
  tone: HistoryTone;
};

type IncidentHistoryProps = {
  incidents: Incident[];
  checks: CheckResult[];
  latencyThresholdMs?: number;
};

const timestampFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "Europe/Berlin",
  timeZoneName: "short",
});

const toneStyles: Record<
  HistoryTone,
  { dot: string; row: string; badge: string }
> = {
  critical: {
    dot: "bg-red-500",
    row: "bg-red-50/50",
    badge: "bg-red-100 text-red-700",
  },
  warning: {
    dot: "bg-amber-400",
    row: "bg-amber-50/70",
    badge: "bg-amber-100 text-amber-700",
  },
  resolved: {
    dot: "bg-emerald-500",
    row: "bg-white",
    badge: "bg-emerald-100 text-emerald-700",
  },
};

function formatTimestamp(value: string): string {
  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) return "Unknown time";
  return timestampFormatter.format(timestamp);
}

function formatLatency(latencyMs: number): string {
  return `${latencyMs.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })} ms`;
}

function incidentItems(incidents: Incident[]): HistoryItem[] {
  return incidents.map((incident) => {
    const isResolved = incident.status === "RESOLVED";
    const isInvestigating = incident.status === "INVESTIGATING";
    const eventTime = incident.resolved_at ?? incident.started_at;
    const failureLabel = `${incident.failure_count} failed ${
      incident.failure_count === 1 ? "check" : "checks"
    }`;

    return {
      key: `incident-${incident.id}`,
      occurredAt: Date.parse(eventTime),
      title: isResolved
        ? "Incident resolved"
        : isInvestigating
          ? "Incident under investigation"
          : "Incident reported",
      description:
        incident.last_error ?? "The monitor failed consecutive checks.",
      metadata: isResolved
        ? `${formatTimestamp(incident.started_at)} – ${formatTimestamp(
            incident.resolved_at ?? incident.started_at,
          )}`
        : `Started ${formatTimestamp(incident.started_at)} · ${failureLabel}`,
      label: isResolved
        ? "Resolved"
        : isInvestigating
          ? "Investigating"
          : "Open incident",
      tone: isResolved ? "resolved" : "critical",
    };
  });
}

function latencyWarningItems(
  checks: CheckResult[],
  latencyThresholdMs: number,
): HistoryItem[] {
  return getSustainedLatencyEpisodes(
    checks,
    latencyThresholdMs,
    LATENCY_WARNING_DURATION_MS,
  ).map((episode) => ({
    key: `latency-${episode.firstCheckId}`,
    occurredAt: Date.parse(episode.alertAt),
    title: "Sustained high response time",
    description: `Latency stayed above ${formatLatency(
      latencyThresholdMs,
    )} for at least 10 minutes and peaked at ${formatLatency(
      episode.peakLatencyMs,
    )}.`,
    metadata: `Alerted ${formatTimestamp(
      episode.alertAt,
    )} · began ${formatTimestamp(episode.startedAt)}`,
    label: "Latency warning",
    tone: "warning",
  }));
}

export default function IncidentHistory({
  incidents,
  checks,
  latencyThresholdMs = LATENCY_WARNING_THRESHOLD_MS,
}: IncidentHistoryProps) {
  const historyItems = [
    ...incidentItems(incidents),
    ...latencyWarningItems(checks, latencyThresholdMs),
  ]
    .sort((left, right) => right.occurredAt - left.occurredAt)
    .slice(0, MAX_HISTORY_ITEMS);

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Incident History</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Incidents and latency above {formatLatency(latencyThresholdMs)} for
            10+ minutes
          </p>
        </div>
        <Link
          href="/incidents"
          className="shrink-0 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          View all&nbsp; →
        </Link>
      </header>

      <div aria-live="polite">
        {historyItems.length === 0 ? (
          <div className="flex min-h-56 items-center justify-center px-6 py-12 text-center">
            <div>
              <span
                aria-hidden="true"
                className="mx-auto flex size-11 items-center justify-center rounded-full bg-emerald-100 text-xl text-emerald-600"
              >
                ✓
              </span>
              <p className="mt-3 font-semibold text-slate-800">
                No incidents or latency warnings yet
              </p>
              <p className="mt-1 max-w-64 text-sm text-slate-500">
                New activity will appear here automatically as checks complete.
              </p>
            </div>
          </div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {historyItems.map((item) => {
              const styles = toneStyles[item.tone];

              return (
                <li key={item.key} className={styles.row}>
                  <div className="flex items-start gap-3 px-5 py-4">
                    <span
                      aria-hidden="true"
                      className={`mt-1.5 size-3 shrink-0 rounded-full ${styles.dot}`}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold text-slate-950">
                          {item.title}
                        </p>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${styles.badge}`}
                        >
                          {item.label}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">
                        {item.description}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.metadata}
                      </p>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
