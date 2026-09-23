"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CheckResult } from "@/lib/api/types";
import { formatBerlinChartTime } from "@/lib/dateTime";

const MAX_CHART_POINTS = 120;

type MonitorResponseTimeChartProps = {
  checks: CheckResult[];
};

export default function MonitorResponseTimeChart({
  checks,
}: MonitorResponseTimeChartProps) {
  const chartData = useMemo(
    () =>
      [...checks]
        .filter((check) => !check.security_rejected)
        .sort(
          (left, right) =>
            Date.parse(left.checked_at) - Date.parse(right.checked_at) ||
            left.id - right.id,
        )
        .slice(-MAX_CHART_POINTS)
        .map((check) => ({
          id: check.id,
          time: formatBerlinChartTime(Date.parse(check.checked_at)),
          latency: check.latency_ms,
        })),
    [checks],
  );

  const maximumLatency = Math.max(
    100,
    ...chartData.map((point) => point.latency),
  );
  const yAxisMaximum = Math.ceil((maximumLatency * 1.1) / 100) * 100;

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-bold text-slate-950">Response Time</h2>
        <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-500">
          Latest {chartData.length} checks
        </span>
      </header>

      {chartData.length === 0 ? (
        <div className="flex h-[230px] items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center">
          <div>
            <p className="font-semibold text-slate-700">No response-time data yet</p>
            <p className="mt-1 text-sm text-slate-500">
              The chart will start plotting points after the first completed check.
            </p>
          </div>
        </div>
      ) : (
        <div className="h-[230px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 8, right: 10, bottom: 0, left: 4 }}
              accessibilityLayer
            >
              <defs>
                <linearGradient id="monitorResponseFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.22} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b", fontSize: 11 }}
                tickMargin={10}
                minTickGap={36}
              />
              <YAxis
                domain={[0, yAxisMaximum]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b", fontSize: 12 }}
                tickFormatter={(value) => `${value} ms`}
                width={65}
              />
              <Tooltip
                cursor={{ stroke: "#93c5fd", strokeDasharray: "4 4" }}
                contentStyle={{
                  border: "1px solid #e2e8f0",
                  borderRadius: "10px",
                  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                }}
                formatter={(value) => [
                  `${Number(value).toFixed(2)} ms`,
                  "Response time",
                ]}
              />
              <Area
                type="monotone"
                dataKey="latency"
                stroke="#2563eb"
                strokeWidth={2.25}
                fill="url(#monitorResponseFill)"
                dot={
                  chartData.length === 1
                    ? { r: 4, fill: "#2563eb", stroke: "#fff", strokeWidth: 2 }
                    : false
                }
                activeDot={{ r: 4, fill: "#2563eb", stroke: "#fff", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </article>
  );
}
