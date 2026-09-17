import Link from "next/link";
import { notFound } from "next/navigation";

import MonitorCheckDashboard from "@/components/monitors/details/MonitorCheckDashboard";
import MonitorHeaderActions from "@/components/monitors/details/MonitorHeaderActions";
import { ApiError } from "@/lib/api/client";
import { getMonitorIncidents } from "@/lib/api/incidents";
import { getMonitor, getMonitorChecks } from "@/lib/api/monitors";
import type { CheckResult, Incident, Monitor } from "@/lib/api/types";

type MonitorDetailsPageProps = {
  params: Promise<{ id: string }>;
};

export default async function MonitorDetailsPage({ params }: MonitorDetailsPageProps) {
  const { id } = await params;
  const monitorId = Number(id);

  if (!Number.isInteger(monitorId) || monitorId <= 0) {
    notFound();
  }

  let monitor: Monitor | null = null;
  let loadError: string | null = null;

  try {
    monitor = await getMonitor(monitorId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }

    loadError = error instanceof Error ? error.message : "The monitor could not be loaded.";
  }

  if (loadError || monitor === null) {
    return (
      <main className="mx-auto w-full max-w-4xl p-4 sm:p-6 lg:p-8">
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700 shadow-sm">
          <h1 className="text-xl font-bold">Could not load this monitor</h1>
          <p className="mt-2 text-sm">
            {loadError} Make sure FastAPI is running at the configured API URL.
          </p>
          <Link href="/monitors" className="mt-4 inline-block font-semibold text-blue-700">
            Return to monitors
          </Link>
        </section>
      </main>
    );
  }

  let initialChecks: CheckResult[] = [];
  let initialIncidents: Incident[] = [];
  let checkHistoryError: string | null = null;
  let incidentHistoryError: string | null = null;

  const [checksResult, incidentsResult] = await Promise.allSettled([
    getMonitorChecks(monitorId),
    getMonitorIncidents(monitorId),
  ]);

  if (checksResult.status === "fulfilled") {
    initialChecks = checksResult.value;
  } else {
    checkHistoryError =
      checksResult.reason instanceof Error
        ? checksResult.reason.message
        : "Check history could not be loaded.";
  }

  if (incidentsResult.status === "fulfilled") {
    initialIncidents = incidentsResult.value;
  } else {
    incidentHistoryError =
      incidentsResult.reason instanceof Error
        ? incidentsResult.reason.message
        : "Incident history could not be loaded.";
  }

  return (
    <main
      data-monitor-id={id}
      className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8"
    >
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/monitors" className="transition hover:text-blue-600">
          Monitors
        </Link>
        <span aria-hidden="true">›</span>
        <span className="font-medium text-slate-700">{monitor.name}</span>
      </nav>

      <section className="mt-3 flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
              {monitor.name}
            </h1>
            <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${monitor.is_active ? "bg-blue-100 text-blue-700" : "bg-amber-100 text-amber-700"}`}>
              <span aria-hidden="true" className={`size-2 rounded-full ${monitor.is_active ? "bg-blue-500" : "bg-amber-500"}`}>
              </span>
              {monitor.is_active ? "Active" : "Paused"}
            </span>
          </div>
          <p className="mt-1 text-slate-600">
            {monitor.purpose || "No purpose has been provided for this monitor."}
          </p>
          <a
            href={monitor.url}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-flex items-center gap-2 font-medium text-blue-600 hover:text-blue-700"
          >
            <span aria-hidden="true">↗</span>
            {monitor.url}
          </a>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
          <MonitorHeaderActions
            monitorId={monitor.id}
            isActive={monitor.is_active}
          />
        </div>
      </section>

      <MonitorCheckDashboard
        key={monitor.id}
        monitor={monitor}
        initialChecks={initialChecks}
        initialIncidents={initialIncidents}
        initialError={checkHistoryError}
        initialIncidentError={incidentHistoryError}
      />
    </main>
  );
}
