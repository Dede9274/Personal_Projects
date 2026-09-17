"use client";

import type { CheckResult } from "@/lib/api/types";

const MAX_TABLE_ROWS = 8;

type RecentChecksProps = {
  checks: CheckResult[];
};

function formatRelativeTime(value: string): string {
  const elapsedSeconds = Math.max(
    0,
    Math.floor((Date.now() - Date.parse(value)) / 1000),
  );

  if (elapsedSeconds < 10) return "just now";
  if (elapsedSeconds < 60) return `${elapsedSeconds} seconds ago`;

  const elapsedMinutes = Math.floor(elapsedSeconds / 60);
  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} ${elapsedMinutes === 1 ? "minute" : "minutes"} ago`;
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60);
  if (elapsedHours < 24) {
    return `${elapsedHours} ${elapsedHours === 1 ? "hour" : "hours"} ago`;
  }

  const elapsedDays = Math.floor(elapsedHours / 24);
  return `${elapsedDays} ${elapsedDays === 1 ? "day" : "days"} ago`;
}

function formatLatency(latencyMs: number): string {
  return `${latencyMs.toLocaleString("en-US", {
    maximumFractionDigits: 2,
  })} ms`;
}

export default function RecentChecks({ checks }: RecentChecksProps) {
  const recentChecks = [...checks]
    .sort(
      (left, right) =>
        Date.parse(right.checked_at) - Date.parse(left.checked_at) ||
        right.id - left.id,
    )
    .slice(0, MAX_TABLE_ROWS);

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-bold text-slate-950">Recent Checks</h2>
        <span className="text-xs font-medium text-slate-500">
          Showing {recentChecks.length} of {checks.length}
        </span>
      </header>

      <div className="w-full">
        <table className="w-full table-fixed text-left text-xs sm:text-sm">
          <colgroup>
            <col className="w-[26%]" />
            <col className="w-[26%]" />
            <col className="w-[28%]" />
            <col className="w-[20%]" />
          </colgroup>
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-2 py-2.5 font-medium sm:px-3">Time</th>
              <th className="px-2 py-2.5 font-medium sm:px-3">Status</th>
              <th className="px-2 py-2.5 font-medium leading-tight sm:px-3">
                Response Time
              </th>
              <th className="px-2 py-2.5 font-medium leading-tight sm:px-3">
                Status Code
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700">
            {recentChecks.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-12 text-center">
                  <p className="font-semibold text-slate-700">No checks recorded yet</p>
                  <p className="mt-1 text-sm text-slate-500">
                    Completed monitor checks will appear here automatically.
                  </p>
                </td>
              </tr>
            ) : (
              recentChecks.map((check) => (
                <tr key={check.id} className="transition hover:bg-slate-50">
                  <td className="px-2 py-2.5 align-top sm:px-3">
                    <time
                      dateTime={check.checked_at}
                      title={new Date(check.checked_at).toISOString()}
                      className="block break-words leading-snug"
                      suppressHydrationWarning
                    >
                      {formatRelativeTime(check.checked_at)}
                    </time>
                  </td>
                  <td className="min-w-0 px-2 py-2.5 align-top sm:px-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold sm:px-3 ${
                        check.success
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {check.success ? "Up" : "Down"}
                    </span>
                    {!check.success && check.error && (
                      <p
                        className="mt-1 block w-full truncate text-[11px] text-red-600"
                        title={check.error}
                      >
                        {check.error}
                      </p>
                    )}
                  </td>
                  <td className="break-words px-2 py-2.5 align-top leading-snug sm:px-3">
                    {formatLatency(check.latency_ms)}
                  </td>
                  <td className="break-words px-2 py-2.5 align-top sm:px-3">
                    {check.status_code ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
