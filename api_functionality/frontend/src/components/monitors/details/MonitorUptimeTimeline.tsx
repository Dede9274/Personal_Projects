"use client";

import { useMemo } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";

import type { CheckResult } from "@/lib/api/types";
import { formatBerlinChartTime } from "@/lib/dateTime";

type TimelineStatus = "up" | "down";

const MAX_CHART_POINTS = 120;
const statusColors: Record<TimelineStatus, string> = {
  up: "#22c55e",
  down: "#ef4444",
};

type MonitorUptimeTimelineProps = {
  checks: CheckResult[];
};

export default function MonitorUptimeTimeline({
  checks,
}: MonitorUptimeTimelineProps) {
  const uptimeData = useMemo(
    () =>
      [...checks]
        .sort(
          (left, right) =>
            Date.parse(left.checked_at) - Date.parse(right.checked_at) ||
            left.id - right.id,
        )
        .slice(-MAX_CHART_POINTS)
        .map((check) => ({
          id: check.id,
          time: formatBerlinChartTime(Date.parse(check.checked_at)),
          availability: 100,
          status: (check.success ? "up" : "down") as TimelineStatus,
        })),
    [checks],
  );

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-bold text-slate-950">Uptime Timeline</h2>
        <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-500">
          Latest {uptimeData.length} checks
        </span>
      </header>

      {uptimeData.length === 0 ? (
        <div className="flex h-[165px] items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center">
          <div>
            <p className="font-semibold text-slate-700">No uptime data yet</p>
            <p className="mt-1 text-sm text-slate-500">
              Up and down markers will appear after checks are completed.
            </p>
          </div>
        </div>
      ) : (
        <div className="h-[165px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={uptimeData}
              barCategoryGap="28%"
              margin={{ top: 12, right: 0, bottom: 0, left: 0 }}
              accessibilityLayer
            >
              <XAxis
                dataKey="time"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b", fontSize: 11 }}
                tickMargin={12}
                minTickGap={42}
              />
              <YAxis hide domain={[0, 100]} />
              <Bar dataKey="availability" radius={[4, 4, 4, 4]} maxBarSize={9}>
                {uptimeData.map((entry) => (
                  <Cell key={entry.id} fill={statusColors[entry.status]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-center gap-5 text-xs text-slate-500">
        {(Object.keys(statusColors) as TimelineStatus[]).map((status) => (
          <span key={status} className="inline-flex items-center gap-1.5 capitalize">
            <span
              aria-hidden="true"
              className="size-2.5 rounded-full"
              style={{ backgroundColor: statusColors[status] }}
            />
            {status}
          </span>
        ))}
      </div>
    </article>
  );
}
