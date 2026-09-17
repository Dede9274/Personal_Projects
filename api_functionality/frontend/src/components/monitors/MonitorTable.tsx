"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { deleteMonitor, updateMonitor } from "@/lib/api/monitors";
import type { Monitor } from "@/lib/api/types";

type MonitorTableProps = {
  monitors: Monitor[];
  hasFilters?: boolean;
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

export default function MonitorTable({
  monitors,
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
          {monitors.length} {monitors.length === 1 ? "monitor" : "monitors"}
        </p>
        <p className="text-xs text-slate-400">
          Health metrics will appear after the check-results API is connected.
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
              <th className="px-3 py-3 font-medium">Monitoring</th>
              <th className="px-3 py-3 font-medium">Response Time</th>
              <th className="px-3 py-3 font-medium">Uptime (30d)</th>
              <th className="px-3 py-3 font-medium">Check Interval</th>
              <th className="px-3 py-3 font-medium">Last Checked</th>
              <th className="w-20 px-5 py-3 text-center font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700">
            {monitors.length === 0 ? (
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
              monitors.map((monitor) => {
                const isBusy = busyMonitorId === monitor.id;

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
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
                          monitor.is_active
                            ? "bg-blue-100 text-blue-700"
                            : "bg-amber-100 text-amber-700"
                        }`}
                      >
                        <span
                          aria-hidden="true"
                          className={`size-2 rounded-full ${
                            monitor.is_active ? "bg-blue-500" : "bg-amber-500"
                          }`}
                        />
                        {monitor.is_active ? "Active" : "Paused"}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-400" title="Check-result summary endpoint not implemented">
                      —
                    </td>
                    <td className="px-3 py-3 text-slate-400" title="Uptime summary endpoint not implemented">
                      —
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      {formatInterval(monitor.interval_seconds)}
                    </td>
                    <td className="px-3 py-3 text-slate-400" title="Latest-check endpoint not implemented">
                      —
                    </td>
                    <td className="px-5 py-3 text-center">
                      <details className="relative inline-block text-left">
                        <summary
                          aria-label={`Actions for ${monitor.name}`}
                          className="flex size-8 cursor-pointer list-none items-center justify-center rounded-lg text-lg font-bold tracking-widest text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600 [&::-webkit-details-marker]:hidden"
                        >
                          <span aria-hidden="true">•••</span>
                        </summary>
                        <div className="absolute right-0 z-20 mt-2 w-40 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 text-left shadow-lg">
                          <Link
                            href={`/monitors/${monitor.id}`}
                            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          >
                            View details
                          </Link>
                          <Link
                            href={`/monitors/${monitor.id}/edit`}
                            className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          >
                            Edit
                          </Link>
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => toggleMonitor(monitor)}
                            className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
                          >
                            {monitor.is_active ? "Pause" : "Resume"}
                          </button>
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => removeMonitor(monitor)}
                            className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 disabled:text-red-300"
                          >
                            Delete
                          </button>
                        </div>
                      </details>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <footer className="border-t border-slate-200 px-5 py-4 text-sm text-slate-500">
        Showing {monitors.length} {monitors.length === 1 ? "monitor" : "monitors"}
      </footer>
    </section>
  );
}
