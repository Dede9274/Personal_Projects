import Link from "next/link";

import type { CheckResult, Monitor } from "@/lib/api/types";
import type { MonitorHealth } from "@/lib/monitorHealth";

export type DashboardMonitorRow = {
  monitor: Monitor;
  latestCheck: CheckResult | null;
  health: MonitorHealth;
};

type MonitorTableProps = {
  rows: DashboardMonitorRow[];
};

const healthStyles: Record<
  MonitorHealth,
  { label: string; badge: string; dot: string }
> = {
  up: {
    label: "Up",
    badge: "bg-emerald-100 text-emerald-700",
    dot: "bg-emerald-500",
  },
  down: {
    label: "Down",
    badge: "bg-red-100 text-red-700",
    dot: "bg-red-500",
  },
  blocked: {
    label: "Blocked",
    badge: "bg-violet-100 text-violet-700",
    dot: "bg-violet-500",
  },
  paused: {
    label: "Paused",
    badge: "bg-amber-100 text-amber-700",
    dot: "bg-amber-500",
  },
  awaiting: {
    label: "Awaiting",
    badge: "bg-slate-100 text-slate-600",
    dot: "bg-slate-400",
  },
  delayed: {
    label: "Delayed",
    badge: "bg-orange-100 text-orange-700",
    dot: "bg-orange-500",
  },
  unavailable: {
    label: "Unavailable",
    badge: "bg-slate-100 text-slate-600",
    dot: "bg-slate-400",
  },
};

function formatLatency(latencyMs: number): string {
  return `${latencyMs.toLocaleString("en-GB", {
    maximumFractionDigits: 0,
  })} ms`;
}

function formatRelativeTime(value: string): string {
  const elapsedSeconds = Math.max(
    0,
    Math.floor((Date.now() - Date.parse(value)) / 1_000),
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

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("");
}

export default function MonitorTable({ rows }: MonitorTableProps) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Monitors</h2>
          <p className="mt-1 text-sm text-slate-500">
            Current status from the latest persisted check
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/monitors"
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            View all
          </Link>
          <Link
            href="/monitors/new"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-500"
          >
            + Add Monitor
          </Link>
        </div>
      </header>

      <table className="w-full table-fixed text-left text-xs sm:text-sm">
        <thead className="bg-slate-50 text-slate-500">
          <tr>
            <th className="w-[32%] px-3 py-3 font-medium sm:px-5">Name</th>
            <th className="hidden w-[28%] px-3 py-3 font-medium lg:table-cell">
              URL
            </th>
            <th className="w-[23%] px-2 py-3 font-medium sm:px-3">Status</th>
            <th className="w-[22%] px-2 py-3 font-medium leading-tight sm:px-3">
              Response Time
            </th>
            <th className="hidden w-[22%] px-3 py-3 font-medium sm:table-cell">
              Last Checked
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-slate-700">
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-5 py-12 text-center">
                <p className="font-semibold text-slate-800">No monitors yet</p>
                <p className="mt-1 text-sm text-slate-500">
                  Add a monitor to start collecting health checks.
                </p>
              </td>
            </tr>
          ) : (
            rows.map(({ monitor, latestCheck, health }) => {
              const styles = healthStyles[health];

              return (
                <tr key={monitor.id} className="transition hover:bg-slate-50">
                  <td className="px-3 py-3 sm:px-5">
                    <div className="flex min-w-0 items-center gap-2 sm:gap-3">
                      <span className="hidden size-8 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-[11px] font-bold text-blue-700 sm:flex">
                        {getInitials(monitor.name)}
                      </span>
                      <div className="min-w-0">
                        <Link
                          href={`/monitors/${monitor.id}`}
                          className="block truncate font-semibold text-slate-950 hover:text-blue-600"
                        >
                          {monitor.name}
                        </Link>
                        {monitor.purpose && (
                          <p className="mt-0.5 hidden truncate text-xs text-slate-500 xl:block">
                            {monitor.purpose}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td
                    className="hidden truncate px-3 py-3 text-slate-500 lg:table-cell"
                    title={monitor.url}
                  >
                    {monitor.url}
                  </td>
                  <td className="px-2 py-3 sm:px-3">
                    <span
                      className={`inline-flex max-w-full items-center gap-1.5 rounded-full px-2 py-1 text-[11px] font-semibold sm:px-2.5 sm:text-xs ${styles.badge}`}
                    >
                      <span
                        aria-hidden="true"
                        className={`size-2 shrink-0 rounded-full ${styles.dot}`}
                      />
                      <span className="truncate">{styles.label}</span>
                    </span>
                  </td>
                  <td className="break-words px-2 py-3 sm:px-3">
                    {latestCheck === null || latestCheck.security_rejected
                      ? "—"
                      : formatLatency(latestCheck.latency_ms)}
                  </td>
                  <td className="hidden px-3 py-3 text-slate-500 sm:table-cell">
                    {latestCheck === null ? (
                      "Never"
                    ) : (
                      <time
                        dateTime={latestCheck.checked_at}
                        title={new Date(latestCheck.checked_at).toISOString()}
                      >
                        {formatRelativeTime(latestCheck.checked_at)}
                      </time>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      <footer className="border-t border-slate-200 px-5 py-3 text-xs text-slate-500">
        {rows.length} current {rows.length === 1 ? "monitor" : "monitors"}
      </footer>
    </section>
  );
}
