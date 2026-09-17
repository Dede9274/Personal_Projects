import MonitorTable from "@/components/monitors/MonitorTable";
import MonitorToolbar from "@/components/monitors/MonitorToolbar";
import { getMonitors } from "@/lib/api/monitors";
import type { Monitor } from "@/lib/api/types";

export const dynamic = "force-dynamic";

type MonitorsPageProps = {
  searchParams: Promise<{
    query?: string;
    status?: string;
    sort?: string;
  }>;
};

function filterAndSortMonitors(
  monitors: Monitor[],
  query: string,
  status: string,
  sort: string,
): Monitor[] {
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = monitors.filter((monitor) => {
    const matchesQuery =
      normalizedQuery.length === 0 ||
      monitor.name.toLowerCase().includes(normalizedQuery) ||
      monitor.url.toLowerCase().includes(normalizedQuery) ||
      monitor.purpose.toLowerCase().includes(normalizedQuery);
    const matchesStatus =
      status === "all" ||
      (status === "active" && monitor.is_active) ||
      (status === "paused" && !monitor.is_active);

    return matchesQuery && matchesStatus;
  });

  return [...filtered].sort((first, second) => {
    if (sort === "name-desc") {
      return second.name.localeCompare(first.name);
    }

    if (sort === "interval-asc") {
      return first.interval_seconds - second.interval_seconds;
    }

    if (sort === "interval-desc") {
      return second.interval_seconds - first.interval_seconds;
    }

    if (sort === "newest") {
      return Date.parse(second.created_at) - Date.parse(first.created_at);
    }

    return first.name.localeCompare(second.name);
  });
}

export default async function MonitorsPage({ searchParams }: MonitorsPageProps) {
  const filters = await searchParams;
  const query = filters.query ?? "";
  const status = filters.status ?? "all";
  const sort = filters.sort ?? "name-asc";

  let monitors: Monitor[] = [];
  let loadError: string | null = null;

  try {
    monitors = await getMonitors();
  } catch (error) {
    loadError =
      error instanceof Error
        ? error.message
        : "The monitor API could not be reached.";
  }

  const visibleMonitors = filterAndSortMonitors(monitors, query, status, sort);
  const activeCount = monitors.filter((monitor) => monitor.is_active).length;
  const pausedCount = monitors.length - activeCount;
  const activePercentage =
    monitors.length === 0 ? 0 : Math.round((activeCount / monitors.length) * 100);

  return (
    <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
            Monitors
          </h1>
          <p className="mt-1 text-base text-slate-500">
            Manage and monitor your endpoints, APIs, and services.
          </p>
        </div>
      </div>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">All Monitors</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{monitors.length}</p>
          <p className="mt-1 text-xs text-slate-500">Stored in PostgreSQL</p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Active Monitors</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{activeCount}</p>
          <p className="mt-1 text-xs text-slate-500">{activePercentage}% scheduled</p>
          <div className="mt-3 h-1.5 rounded-full bg-blue-100">
            <div
              className="h-1.5 rounded-full bg-blue-500"
              style={{ width: `${activePercentage}%` }}
            />
          </div>
        </article>

        <article className="rounded-xl border border-amber-100 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Paused Monitors</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">{pausedCount}</p>
          <p className="mt-1 text-xs text-slate-500">Not scheduled for checks</p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-[15px] font-semibold text-slate-500">Visible Results</p>
          <p className="mt-2 text-[30px] leading-none font-bold text-slate-900">
            {visibleMonitors.length}
          </p>
          <p className="mt-1 text-xs text-slate-500">After current filters</p>
        </article>
      </section>

      <MonitorToolbar
        key={query}
        query={query}
        status={status}
        sort={sort}
      />

      {loadError ? (
        <section className="mt-4 rounded-xl border border-red-200 bg-red-50 p-6 text-red-700 shadow-sm">
          <h2 className="font-bold">Could not load monitors</h2>
          <p className="mt-1 text-sm">
            {loadError} Make sure FastAPI is running at the configured API URL.
          </p>
        </section>
      ) : (
        <MonitorTable
          monitors={visibleMonitors}
          hasFilters={query.trim().length > 0 || status !== "all"}
        />
      )}
    </main>
  );
}
