import Link from "next/link";

type IncidentSeverity = "critical" | "resolved";

export type IncidentNotification = {
  id: number;
  title: string;
  message: string;
  occurredAt: string;
  occurredAtIso: string;
  severity: IncidentSeverity;
};

type RecentIncidentsProps = {
  incidents: IncidentNotification[];
  loadError?: string | null;
};

const severityDotClasses: Record<IncidentSeverity, string> = {
  critical: "bg-red-500",
  resolved: "bg-emerald-500",
};

function IncidentRow({ incident }: { incident: IncidentNotification }) {
  return (
    <li>
      <Link
        href="/incidents"
        className="group grid w-full grid-cols-[auto_minmax(0,1fr)_auto_auto] items-center gap-3 px-5 py-3 text-left transition-colors hover:bg-slate-50"
      >
        <span
          className={`size-3 rounded-full ${severityDotClasses[incident.severity]}`}
          aria-hidden="true"
        />
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold text-slate-950">
            {incident.title}
          </span>
          <span className="mt-0.5 block truncate text-xs text-slate-500">
            {incident.message}
          </span>
        </span>
        <time
          dateTime={incident.occurredAtIso}
          className="whitespace-nowrap text-xs text-slate-500"
        >
          {incident.occurredAt}
        </time>
        <span
          className="text-xl leading-none text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-600"
          aria-hidden="true"
        >
          ›
        </span>
      </Link>
    </li>
  );
}

export default function RecentIncidents({
  incidents,
  loadError = null,
}: RecentIncidentsProps) {
  return (
    <section className="h-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-950">
          Recent Incidents
        </h2>
        <Link
          href="/incidents"
          className="text-sm font-medium text-blue-600 hover:text-blue-500"
        >
          View all <span aria-hidden="true">→</span>
        </Link>
      </header>

      {loadError ? (
        <div className="px-5 py-12 text-center">
          <p className="text-sm font-medium text-red-700">
            Incident data is unavailable
          </p>
          <p className="mt-1 text-xs text-slate-500">{loadError}</p>
        </div>
      ) : incidents.length > 0 ? (
        <ul className="divide-y divide-slate-100">
          {incidents.map((incident) => (
            <IncidentRow key={incident.id} incident={incident} />
          ))}
        </ul>
      ) : (
        <div className="px-5 py-12 text-center">
          <p className="text-sm font-medium text-slate-700">
            No recent incidents
          </p>
          <p className="mt-1 text-xs text-slate-500">
            No incident has been recorded for the current monitors.
          </p>
        </div>
      )}
    </section>
  );
}
