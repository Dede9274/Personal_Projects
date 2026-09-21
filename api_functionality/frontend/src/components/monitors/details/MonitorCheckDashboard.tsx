"use client";

import { useEffect, useMemo, useState } from "react";

import IncidentHistory from "@/components/monitors/details/IncidentHistory";
import MonitorConfiguration from "@/components/monitors/details/MonitorConfiguration";
import MonitorResponseTimeChart from "@/components/monitors/details/MonitorResponseTimeChart";
import MonitorUptimeTimeline from "@/components/monitors/details/MonitorUptimeTimeline";
import RecentChecks from "@/components/monitors/details/RecentChecks";
import { getMonitorIncidents } from "@/lib/api/incidents";
import { getMonitorChecks } from "@/lib/api/monitors";
import type { CheckResult, Incident, Monitor } from "@/lib/api/types";

const POLL_INTERVAL_MS = 5_000;

type MonitorCheckDashboardProps = {
  monitor: Monitor;
  initialChecks: CheckResult[];
  initialIncidents: Incident[];
  initialError?: string | null;
  initialIncidentError?: string | null;
};

function newestFirst(checks: CheckResult[]): CheckResult[] {
  return [...checks].sort(
    (left, right) =>
      Date.parse(right.checked_at) - Date.parse(left.checked_at) ||
      right.id - left.id,
  );
}

function formatLatency(latencyMs: number): string {
  return `${latencyMs.toLocaleString("en-US", {
    maximumFractionDigits: 2,
  })} ms`;
}

export default function MonitorCheckDashboard({
  monitor,
  initialChecks,
  initialIncidents,
  initialError = null,
  initialIncidentError = null,
}: MonitorCheckDashboardProps) {
  const [checks, setChecks] = useState(() => newestFirst(initialChecks));
  const [incidents, setIncidents] = useState(initialIncidents);
  const [refreshError, setRefreshError] = useState<string | null>(() => {
    const errors = [initialError, initialIncidentError].filter(Boolean);
    return errors.length > 0 ? errors.join(" ") : null;
  });
  const [lastRefreshAt, setLastRefreshAt] = useState<number | null>(null);

  useEffect(() => {
    let stopped = false;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    let activeRequest: AbortController | undefined;

    async function refreshDashboard() {
      activeRequest = new AbortController();

      const [checksResult, incidentsResult] = await Promise.allSettled([
        getMonitorChecks(monitor.id, {
          limit: 500,
          signal: activeRequest.signal,
        }),
        getMonitorIncidents(monitor.id, {
          signal: activeRequest.signal,
        }),
      ]);

      if (!stopped) {
        const errors: string[] = [];

        if (checksResult.status === "fulfilled") {
          setChecks(newestFirst(checksResult.value));
          setLastRefreshAt(Date.now());
        } else if (
          !(
            checksResult.reason instanceof Error &&
            checksResult.reason.name === "AbortError"
          )
        ) {
          errors.push(
            checksResult.reason instanceof Error
              ? checksResult.reason.message
              : "Check history could not be refreshed.",
          );
        }

        if (incidentsResult.status === "fulfilled") {
          setIncidents(incidentsResult.value);
        } else if (
          !(
            incidentsResult.reason instanceof Error &&
            incidentsResult.reason.name === "AbortError"
          )
        ) {
          errors.push(
            incidentsResult.reason instanceof Error
              ? incidentsResult.reason.message
              : "Incident history could not be refreshed.",
          );
        }

        setRefreshError(errors.length > 0 ? errors.join(" ") : null);
      }

      if (!stopped) {
        timeoutId = setTimeout(refreshDashboard, POLL_INTERVAL_MS);
      }
    }

    void refreshDashboard();

    return () => {
      stopped = true;
      if (timeoutId !== undefined) clearTimeout(timeoutId);
      activeRequest?.abort();
    };
  }, [monitor.id]);

  const metrics = useMemo(() => {
    const latestCheck = checks[0] ?? null;
    const availabilityChecks = checks.filter(
      (check) => !check.security_rejected,
    );

    if (availabilityChecks.length === 0) {
      return {
        latestCheck,
        averageLatency: null,
        successRate: null,
      };
    }

    const totalLatency = availabilityChecks.reduce(
      (total, check) => total + check.latency_ms,
      0,
    );
    const successfulChecks = availabilityChecks.filter(
      (check) => check.success,
    ).length;

    return {
      latestCheck,
      averageLatency: totalLatency / availabilityChecks.length,
      successRate: (successfulChecks / availabilityChecks.length) * 100,
    };
  }, [checks]);

  const currentState = !monitor.is_active
    ? "Paused"
    : metrics.latestCheck === null
      ? "Awaiting check"
      : metrics.latestCheck.security_rejected
        ? "Blocked"
      : metrics.latestCheck.success
        ? "Up"
        : "Down";
  const statusTone = !monitor.is_active
    ? "bg-amber-100 text-amber-600"
    : metrics.latestCheck === null
      ? "bg-slate-100 text-slate-500"
      : metrics.latestCheck.security_rejected
        ? "bg-violet-100 text-violet-700"
      : metrics.latestCheck.success
        ? "bg-emerald-100 text-emerald-600"
        : "bg-red-100 text-red-600";
  const latestCheckTimestamp = metrics.latestCheck
    ? Date.parse(metrics.latestCheck.checked_at)
    : Date.parse(monitor.created_at);
  const expectedCheckWindowMs = Math.max(
    monitor.interval_seconds * 3 * 1_000,
    30_000,
  );
  const checksAreDelayed =
    monitor.is_active &&
    lastRefreshAt !== null &&
    lastRefreshAt - latestCheckTimestamp > expectedCheckWindowMs;

  const engineMessage = !monitor.is_active
    ? "Monitoring is paused. No new checks will be scheduled until this monitor is resumed."
    : checksAreDelayed
      ? "Checks are delayed. The scheduler or monitor worker may not be running."
      : metrics.latestCheck === null
        ? "Waiting for the first completed check from the scheduler and monitor worker."
        : metrics.latestCheck.security_rejected
          ? metrics.latestCheck.error ??
            "The latest check was blocked by the outbound request security policy."
        : `Monitoring is active. Latest check: ${new Date(
            metrics.latestCheck.checked_at,
          ).toISOString()}.`;

  return (
    <>
      {refreshError && (
        <div
          role="alert"
          className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        >
          <p>
            Live check data could not be refreshed. The last successfully loaded data is still shown.
            <span className="ml-1 font-medium">{refreshError}</span>
          </p>
          <span className="shrink-0" aria-label="Retrying automatically">
            Retrying…
          </span>
        </div>
      )}

      <div
        role={
          checksAreDelayed || metrics.latestCheck?.security_rejected
            ? "alert"
            : "status"
        }
        className={`mt-6 flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${
          checksAreDelayed
            ? "border-amber-200 bg-amber-50 text-amber-800"
            : metrics.latestCheck?.security_rejected
              ? "border-violet-200 bg-violet-50 text-violet-800"
            : monitor.is_active
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-slate-200 bg-slate-50 text-slate-600"
        }`}
      >
        <span
          aria-hidden="true"
          className={`size-2.5 shrink-0 rounded-full ${
            checksAreDelayed
              ? "bg-amber-500"
              : metrics.latestCheck?.security_rejected
                ? "bg-violet-500"
              : monitor.is_active
                ? "bg-emerald-500"
                : "bg-slate-400"
          }`}
        />
        <p>
          {engineMessage}
          <span className="ml-1 text-xs opacity-75">
            Dashboard data refreshes every 5 seconds.
          </span>
        </p>
      </div>

      <section
        aria-label="Monitor statistics"
        className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <article className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <span
            aria-hidden="true"
            className={`flex size-14 shrink-0 items-center justify-center rounded-xl text-2xl font-bold ${statusTone}`}
          >
            {currentState === "Up"
              ? "✓"
              : currentState === "Down"
                ? "×"
                : currentState === "Blocked"
                  ? "!"
                  : "◷"}
          </span>
          <div>
            <p className="text-[15px] font-semibold text-slate-500">Current Status</p>
            <p className="mt-1 text-[28px] leading-none font-bold text-slate-900">{currentState}</p>
            <p className="text-xs text-slate-500">
              {metrics.latestCheck === null
                ? "No completed checks"
                : metrics.latestCheck.security_rejected
                  ? "Request not sent"
                : `HTTP ${metrics.latestCheck.status_code ?? "unavailable"}`}
            </p>
          </div>
        </article>

        <article className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <span aria-hidden="true" className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <span className="relative size-6 rounded-full border-2 border-current">
              <span className="absolute left-1/2 top-1/2 h-0.5 w-2 origin-left -translate-y-1/2 -rotate-45 rounded-full bg-current" />
              <span className="absolute left-1/2 top-1/2 size-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-current" />
            </span>
          </span>
          <div>
            <p className="text-[15px] font-semibold text-slate-500">Response Time (Avg)</p>
            <p className="mt-1 text-[28px] leading-none font-bold text-slate-900">
              {metrics.averageLatency === null
                ? "—"
                : formatLatency(metrics.averageLatency)}
            </p>
            <p className="text-xs text-slate-500">Latest loaded checks</p>
          </div>
        </article>

        <article className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <span aria-hidden="true" className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-2xl font-bold text-emerald-600">
            ▥
          </span>
          <div>
            <p className="text-[15px] font-semibold text-slate-500">Success Rate</p>
            <p className="mt-1 text-[28px] leading-none font-bold text-slate-900">
              {metrics.successRate === null
                ? "—"
                : `${metrics.successRate.toFixed(2)}%`}
            </p>
            <p className="text-xs text-slate-500">Latest loaded checks</p>
          </div>
        </article>

        <article className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <span aria-hidden="true" className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-2xl font-bold text-blue-600">
            ◷
          </span>
          <div>
            <p className="text-[15px] font-semibold text-slate-500">Loaded Checks</p>
            <p className="mt-1 text-[28px] leading-none font-bold text-slate-900">
              {checks.length.toLocaleString("en-US")}
            </p>
            <p className="text-xs text-slate-500">Updates every 5 seconds</p>
          </div>
        </article>
      </section>

      <section
        aria-label="Monitor performance charts"
        className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(380px,1fr)]"
      >
        <MonitorResponseTimeChart checks={checks} />
        <MonitorUptimeTimeline checks={checks} />
      </section>

      <section
        aria-label="Monitor activity and configuration"
        className="mt-4 grid items-start gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.95fr)_minmax(360px,1.1fr)]"
      >
        <RecentChecks checks={checks} />
        <IncidentHistory incidents={incidents} checks={checks} />
        <MonitorConfiguration monitor={monitor} />
      </section>
    </>
  );
}
