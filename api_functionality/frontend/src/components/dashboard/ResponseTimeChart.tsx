"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type ResponseTimePoint = {
  time: string;
  responseTime: number;
};

type ResponseTimeChartProps = {
  data: ResponseTimePoint[];
};

export default function ResponseTimeChart({
  data,
}: ResponseTimeChartProps) {
  const maximumLatency = Math.max(
    100,
    ...data.map((point) => point.responseTime),
  );
  const yAxisMaximum = Math.ceil((maximumLatency * 1.1) / 100) * 100;

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">
            Response Time (Average)
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Average latency from recent successful monitor checks
          </p>
        </div>
        <span className="w-fit rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-500">
          Recent saved checks
        </span>
      </header>

      {data.length === 0 ? (
        <div className="flex h-[280px] items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center">
          <div>
            <p className="font-semibold text-slate-700">
              No response-time data yet
            </p>
            <p className="mt-1 text-sm text-slate-500">
              The chart will appear after successful checks are saved.
            </p>
          </div>
        </div>
      ) : (
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 8, right: 12, bottom: 0, left: 4 }}
              accessibilityLayer
            >
              <defs>
                <linearGradient
                  id="responseTimeFill"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.22} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b", fontSize: 12 }}
                tickMargin={12}
                minTickGap={36}
              />
              <YAxis
                domain={[0, yAxisMaximum]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b", fontSize: 12 }}
                tickFormatter={(value) => `${value} ms`}
                width={64}
              />
              <Tooltip
                cursor={{ stroke: "#93c5fd", strokeDasharray: "4 4" }}
                contentStyle={{
                  border: "1px solid #e2e8f0",
                  borderRadius: "10px",
                  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                }}
                labelStyle={{ color: "#475569", marginBottom: "4px" }}
              />
              <Area
                type="monotone"
                dataKey="responseTime"
                name="Average response"
                unit=" ms"
                stroke="#2563eb"
                strokeWidth={2.25}
                fill="url(#responseTimeFill)"
                dot={
                  data.length === 1
                    ? {
                        r: 4,
                        fill: "#2563eb",
                        stroke: "#ffffff",
                        strokeWidth: 2,
                      }
                    : false
                }
                activeDot={{
                  r: 4,
                  fill: "#2563eb",
                  stroke: "#ffffff",
                  strokeWidth: 2,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </article>
  );
}
