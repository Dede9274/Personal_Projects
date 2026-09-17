"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

type MonitorStatus = "UP" | "DOWN" | "PAUSED";

type MonitorStatusChartProps = {
  up: number;
  down: number;
  paused: number;
};

const COLORS: Record<MonitorStatus, string> = {
  UP: "#16a34a",
  DOWN: "#dc2626",
  PAUSED: "#d97706",
};

const STATUS_LABELS: Record<MonitorStatus, string> = {
  UP: "Up",
  DOWN: "Down",
  PAUSED: "Paused",
};

export default function MonitorStatusChart({
  up,
  down,
  paused,
}: MonitorStatusChartProps) {
  const data: Array<{ name: MonitorStatus; value: number }> = [
    { name: "UP", value: up },
    { name: "DOWN", value: down },
    { name: "PAUSED", value: paused },
  ];

  const total = up + down + paused;
  const percentage = (value: number) =>
    total === 0 ? 0 : Math.round((value / total) * 100);

  return (
    <article className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Monitor Status</h2>

      <div className="mt-5 flex flex-1 flex-col items-center justify-center gap-5 sm:flex-row xl:gap-3">
        <div
          className="h-48 w-48 shrink-0"
          role="img"
          aria-label={`${up} monitors up, ${down} down, and ${paused} paused`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={56}
                outerRadius={76}
                startAngle={90}
                endAngle={-270}
                stroke="#ffffff"
                strokeWidth={2}
                isAnimationActive={false}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name]} />
                ))}
              </Pie>

              <Tooltip
                contentStyle={{
                  border: "1px solid #e2e8f0",
                  borderRadius: "10px",
                  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                }}
                formatter={(value) => [`${value}`, "Monitors"]}
                labelFormatter={(label) => STATUS_LABELS[label as MonitorStatus]}
              />

              <text
                x="50%"
                y="47%"
                textAnchor="middle"
                dominantBaseline="central"
                fill="#0f172a"
                fontSize="27"
                fontWeight="700"
              >
                {total}
              </text>
              <text
                x="50%"
                y="60%"
                textAnchor="middle"
                dominantBaseline="central"
                fill="#64748b"
                fontSize="13"
              >
                Total
              </text>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <ul className="w-full min-w-0 space-y-2 sm:max-w-44">
          {data.map((entry) => (
            <li
              key={entry.name}
              className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 px-3 py-2.5 text-sm"
            >
              <span className="flex items-center gap-2 text-slate-600">
                <span
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: COLORS[entry.name] }}
                />
                {STATUS_LABELS[entry.name]}
              </span>

              <span className="whitespace-nowrap font-semibold text-slate-950">
                {entry.value} ({percentage(entry.value)}%)
              </span>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}
