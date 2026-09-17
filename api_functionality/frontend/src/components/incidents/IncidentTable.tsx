import IncidentStatusActions from "@/components/incidents/IncidentStatusActions";
import type {
  IncidentActivity,
  IncidentActivityStatus,
  IncidentSeverity,
} from "@/lib/incidentActivity";

type IncidentTableProps = {
  incidents: IncidentActivity[];
  totalCount: number;
  now: number;
};

const severityStyles: Record<IncidentSeverity, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
};

const severityDots: Record<IncidentSeverity, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-amber-400",
  low: "bg-emerald-500",
};

const statusStyles: Record<IncidentActivityStatus, string> = {
  open: "bg-red-100 text-red-700",
  investigating: "bg-blue-100 text-blue-700",
  resolved: "bg-emerald-100 text-emerald-700",
};

const berlinDateTimeFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "Europe/Berlin",
  timeZoneName: "short",
});

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function formatStarted(value: string, now: number): string {
  const startedAt = Date.parse(value);
  if (Number.isNaN(startedAt)) return "Unknown";

  const elapsedSeconds = Math.max(0, Math.floor((now - startedAt) / 1_000));
  if (elapsedSeconds < 60) return "Just now";

  const minutes = Math.floor(elapsedSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;

  return berlinDateTimeFormatter.format(startedAt);
}

function formatDuration(durationMs: number): string {
  const totalMinutes = Math.max(0, Math.floor(durationMs / 60_000));
  if (totalMinutes < 1) return "<1m";
  if (totalMinutes < 60) return `${totalMinutes}m`;

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours < 24) {
    return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours === 0
    ? `${days}d`
    : `${days}d ${remainingHours}h`;
}

function IncidentRow({
  incident,
  now,
}: {
  incident: IncidentActivity;
  now: number;
}) {
  const startedAt = Date.parse(incident.startedAt);
  const exactStart = Number.isNaN(startedAt)
    ? "Unknown time"
    : berlinDateTimeFormatter.format(startedAt);

  return (
    <tr className="transition hover:bg-slate-50">
      <td className="min-w-64 px-4 py-3">
        <div className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className={`mt-1.5 size-3 shrink-0 rounded-full ${severityDots[incident.severity]}`}
          />
          <div>
            <p className="font-semibold text-slate-950">{incident.title}</p>
            <p className="mt-0.5 max-w-md text-xs text-slate-500">
              {incident.error}
            </p>
          </div>
        </div>
      </td>
      <td className="min-w-52 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-[10px] font-bold text-white">
            {getInitials(incident.monitorName)}
          </span>
          <div className="min-w-0">
            <p className="font-medium text-slate-900">
              {incident.monitorName}
            </p>
            <p className="max-w-52 truncate text-xs text-slate-500">
              {incident.monitorUrl}
            </p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${severityStyles[incident.severity]}`}
        >
          <span aria-hidden="true" className="size-2 rounded-full bg-current" />
          {incident.severity}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusStyles[incident.status]}`}
        >
          <span aria-hidden="true" className="size-2 rounded-full bg-current" />
          {incident.status}
        </span>
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-slate-600">
        <time dateTime={incident.startedAt} title={exactStart}>
          {formatStarted(incident.startedAt, now)}
        </time>
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-slate-600">
        {formatDuration(incident.durationMs)}
      </td>
      <td className="px-4 py-3 text-right">
        <IncidentStatusActions
          incidentId={incident.incidentId}
          monitorId={incident.monitorId}
          title={incident.title}
          status={incident.status}
        />
      </td>
    </tr>
  );
}

export default function IncidentTable({
  incidents,
  totalCount,
  now,
}: IncidentTableProps) {
  const isFiltered = incidents.length !== totalCount;

  return (
    <section className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <header className="flex flex-col gap-1 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-950">
            Incidents and latency events ({incidents.length})
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Severity is calculated from current monitor data.
          </p>
        </div>
        {isFiltered && (
          <p className="text-sm text-slate-500">{totalCount} total events</p>
        )}
      </header>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1040px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Title</th>
              <th className="px-4 py-3 font-medium">Affected Monitor</th>
              <th className="px-4 py-3 font-medium">Severity</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Started</th>
              <th className="px-4 py-3 font-medium">Duration</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700">
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-14 text-center">
                  <p className="font-semibold text-slate-900">
                    No matching incidents
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    New outages and latency warnings will appear as checks run.
                  </p>
                </td>
              </tr>
            ) : (
              incidents.map((incident) => (
                <IncidentRow key={incident.key} incident={incident} now={now} />
              ))
            )}
          </tbody>
        </table>
      </div>

      <footer className="border-t border-slate-200 px-5 py-4 text-sm text-slate-500">
        Showing {incidents.length} of {totalCount} events
      </footer>
    </section>
  );
}
