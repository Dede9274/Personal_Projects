import type { ReactNode } from "react";
import Link from "next/link";

import type { Monitor } from "@/lib/api/types";

type ConfigurationRowProps = {
  icon: string;
  label: string;
  children: ReactNode;
};

function ConfigurationRow({ icon, label, children }: ConfigurationRowProps) {
  return (
    <div className="grid grid-cols-[24px_minmax(120px,0.85fr)_minmax(0,1.2fr)] items-start gap-3 px-5 py-2.5 text-sm">
      <span aria-hidden="true" className="text-center font-semibold text-slate-500">
        {icon}
      </span>
      <dt className="text-slate-500">{label}</dt>
      <dd className="min-w-0 font-medium text-slate-900">{children}</dd>
    </div>
  );
}

function formatInterval(seconds: number): string {
  if (seconds >= 60 && seconds % 60 === 0) {
    const minutes = seconds / 60;
    return `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
  }

  return `${seconds} ${seconds === 1 ? "second" : "seconds"}`;
}

type MonitorConfigurationProps = {
  monitor: Monitor;
};

export default function MonitorConfiguration({
  monitor,
}: MonitorConfigurationProps) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-bold text-slate-950">Monitor Configuration</h2>
        <Link
          href={`/monitors/${monitor.id}/edit`}
          className="inline-flex h-9 items-center rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
        >
          ✎&nbsp; Edit
        </Link>
      </header>

      <dl className="py-2">
        <ConfigurationRow icon="▣" label="Monitor Name">
          {monitor.name}
        </ConfigurationRow>
        <ConfigurationRow icon="i" label="Purpose">
          {monitor.purpose || "No purpose provided"}
        </ConfigurationRow>
        <ConfigurationRow icon="↗" label="URL">
          <a
            href={monitor.url}
            target="_blank"
            rel="noreferrer"
            className="break-all text-blue-600 hover:text-blue-700"
          >
            {monitor.url}
          </a>
        </ConfigurationRow>
        <ConfigurationRow icon="◷" label="Check Interval">
          {formatInterval(monitor.interval_seconds)}
        </ConfigurationRow>
        <ConfigurationRow icon="◴" label="Timeout">
          {monitor.timeout_seconds} seconds
        </ConfigurationRow>
        <ConfigurationRow icon="&lt;/&gt;" label="Expected Status Code">
          {monitor.expected_status_code}
        </ConfigurationRow>
        <ConfigurationRow icon="◉" label="Scheduler">
          {monitor.is_active ? "Active" : "Paused"}
        </ConfigurationRow>
      </dl>
    </section>
  );
}
