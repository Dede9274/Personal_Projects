"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import ActionMenu from "@/components/ui/ActionMenu";
import { deleteMonitor, updateMonitor } from "@/lib/api/monitors";
import type { CheckResult, Monitor } from "@/lib/api/types";
import type { MonitorHealth } from "@/lib/monitorHealth";

export type MonitorTableRow = {
  monitor: Monitor;
  latestCheck: CheckResult | null;
  checksLoaded: boolean;
  health: MonitorHealth;
  recentUptime: number | null;
};

type MonitorTableProps = {
  rows: MonitorTableRow[];
  now: number;
  hasFilters?: boolean;
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

function formatInterval(seconds: number): string {
  if (seconds >= 60 && seconds % 60 === 0) {
    const minutes = seconds / 60;
    return `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
  }

  return `${seconds} ${seconds === 1 ? "second" : "seconds"}`;
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("");
}

function formatLatency(latencyMs: number): string {
  return `${latencyMs.toLocaleString("en-GB", {
    maximumFractionDigits: 0,
  })} ms`;
}

function formatUptime(uptime: number): string {
  const digits = uptime === 100 || uptime === 0 ? 0 : 1;
  return `${uptime.toFixed(digits)}%`;
}

function formatRelativeTime(value: string, now: number): string {
  const checkedAt = Date.parse(value);
  if (Number.isNaN(checkedAt)) return "Unknown";

  const elapsedSeconds = Math.max(
    0,
    Math.floor((now - checkedAt) / 1_000),
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

export default function MonitorTable({
  rows,
  now,
  hasFilters = false,
}: MonitorTableProps) {
  const router = useRouter();
  const [busyMonitorId, setBusyMonitorId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function toggleMonitor(monitor: Monitor) {
    setBusyMonitorId(monitor.id);
    setActionError(null);

    try {
      await updateMonitor(monitor.id, { is_active: !monitor.is_active });
      router.refresh();
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "The monitor could not be updated.",
      );
    } finally {
      setBusyMonitorId(null);
    }
  }

  async function removeMonitor(monitor: Monitor) {
    const confirmed = window.confirm(
      `Delete ${monitor.name}? Its checks and incidents will also be deleted.`,
    );

    if (!confirmed) {
      return;
    }

    setBusyMonitorId(monitor.id);
    setActionError(null);

    try {
      await deleteMonitor(monitor.id);
      router.refresh();
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "The monitor could not be deleted.",
      );
    } finally {
      setBusyMonitorId(null);
    }
  }

  return (
    <section className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex min-h-14 items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
        <p className="text-sm text-slate-500">
          {rows.length} {rows.length === 1 ? "monitor" : "monitors"}
        </p>
        <p className="text-xs text-slate-400">
          Health metrics use up to the latest 500 persisted checks.
        </p>
      </div>

      {actionError && (
        <div role="alert" className="border-b border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1160px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-3 py-3 font-medium">URL</th>
              <th className="px-3 py-3 font-medium">Status</th>
              <th className="px-3 py-3 font-medium">Response Time</th>
              <th className="px-3 py-3 font-medium">Recent Uptime</th>
              <th className="px-3 py-3 font-medium">Check Interval</th>
              <th className="px-3 py-3 font-medium">Last Checked</th>
              <th className="w-20 px-5 py-3 text-center font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-5 py-14 text-center">
                  <p className="font-semibold text-slate-900">
                    {hasFilters ? "No matching monitors" : "No monitors yet"}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {hasFilters
                      ? "Try another search term or clear the current filters."
                      : "Create your first monitor or run the backend seed command."}
                  </p>
                  <Link
                    href={hasFilters ? "/monitors" : "/monitors/new"}
                    className="mt-4 inline-flex h-10 items-center rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white transition hover:bg-blue-700"
                  >
                    {hasFilters ? "Clear filters" : "Add Monitor"}
                  </Link>
                </td>
              </tr>
            ) : (
              rows.map(({ monitor, latestCheck, checksLoaded, health, recentUptime }) => {
                const isBusy = busyMonitorId === monitor.id;
                const styles = healthStyles[health];

                return (
                  <tr key={monitor.id} className="transition hover:bg-slate-50/80">
                    <td className="whitespace-nowrap px-5 py-3">
                      <div className="flex items-center gap-3">
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-[11px] font-bold text-blue-700">
                          {getInitials(monitor.name)}
                        </span>
                        <div>
                          <Link
                            href={`/monitors/${monitor.id}`}
                            className="font-semibold text-slate-950 hover:text-blue-600"
                          >
                            {monitor.name}
                          </Link>
                          {monitor.purpose && (
                            <p className="mt-0.5 max-w-56 truncate text-xs text-slate-500">
                              {monitor.purpose}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="max-w-72 truncate px-3 py-3 text-slate-500">
                      {monitor.url}
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${styles.badge}`}
                      >
                        <span
                          aria-hidden="true"
                          className={`size-2 rounded-full ${styles.dot}`}
                        />
                        {styles.label}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      {latestCheck === null
                        ? "—"
                        : formatLatency(latestCheck.latency_ms)}
                    </td>
                    <td
                      className="whitespace-nowrap px-3 py-3"
                      title="Calculated from up to the latest 500 persisted checks"
                    >
                      {recentUptime === null ? "—" : formatUptime(recentUptime)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      {formatInterval(monitor.interval_seconds)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-slate-500">
                      {!checksLoaded ? (
                        "Unavailable"
                      ) : latestCheck === null ? (
                        "Never"
                      ) : (
                        <time
                          dateTime={latestCheck.checked_at}
                          title={new Date(latestCheck.checked_at).toISOString()}
                        >
                          {formatRelativeTime(latestCheck.checked_at, now)}
                        </time>
                      )}
                    </td>
                    <td className="px-5 py-3 text-center">
                      <div className="inline-flex">
                        <ActionMenu label={`Actions for ${monitor.name}`} menuClassName="w-40">
                          <Link
                            href={`/monitors/${monitor.id}`}
                            role="menuitem"
                            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          >
                            View details
                          </Link>
                          <Link
                            href={`/monitors/${monitor.id}/edit`}
                            role="menuitem"
                            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          >
                            Edit
                          </Link>
                          <button
                            type="button"
                            role="menuitem"
                            disabled={isBusy}
                            onClick={() => toggleMonitor(monitor)}
                            className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
                          >
                            {monitor.is_active ? "Pause" : "Resume"}
                          </button>
                          <button
                            type="button"
                            role="menuitem"
                            disabled={isBusy}
                            onClick={() => removeMonitor(monitor)}
                            className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 disabled:text-red-300"
                          >
                            Delete
                          </button>
                        </ActionMenu>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <footer className="border-t border-slate-200 px-5 py-4 text-sm text-slate-500">
        Showing {rows.length} {rows.length === 1 ? "monitor" : "monitors"}
      </footer>
    </section>
  );
}
