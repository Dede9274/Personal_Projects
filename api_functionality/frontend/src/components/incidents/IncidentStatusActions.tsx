"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import ActionMenu from "@/components/ui/ActionMenu";
import { updateIncidentStatus } from "@/lib/api/incidents";
import type { IncidentStatus } from "@/lib/api/types";
import type { IncidentActivityStatus } from "@/lib/incidentActivity";

type IncidentStatusActionsProps = {
  incidentId: number | null;
  monitorId: number;
  title: string;
  status: IncidentActivityStatus;
};

type StatusAction = {
  status: IncidentStatus;
  label: string;
  className: string;
};

const resolveAction: StatusAction = {
  status: "RESOLVED",
  label: "Mark resolved",
  className: "text-emerald-700 hover:bg-emerald-50",
};

function availableActions(status: IncidentActivityStatus): StatusAction[] {
  if (status === "open") {
    return [
      {
        status: "INVESTIGATING",
        label: "Mark investigating",
        className: "text-blue-700 hover:bg-blue-50",
      },
      resolveAction,
    ];
  }

  if (status === "investigating") {
    return [
      {
        status: "OPEN",
        label: "Mark open",
        className: "text-orange-700 hover:bg-orange-50",
      },
      resolveAction,
    ];
  }

  return [];
}

export default function IncidentStatusActions({
  incidentId,
  monitorId,
  title,
  status,
}: IncidentStatusActionsProps) {
  const router = useRouter();
  const [pendingStatus, setPendingStatus] = useState<IncidentStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const actions = incidentId === null ? [] : availableActions(status);

  async function changeStatus(newStatus: IncidentStatus) {
    if (incidentId === null || pendingStatus !== null) return;

    setError(null);
    setPendingStatus(newStatus);

    try {
      await updateIncidentStatus(incidentId, newStatus);
      router.refresh();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The incident status could not be updated.",
      );
    } finally {
      setPendingStatus(null);
    }
  }

  return (
    <div className="relative inline-flex flex-col items-end">
      <ActionMenu label={`Actions for ${title}`}>
        <Link
          href={`/monitors/${monitorId}`}
          role="menuitem"
          className="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
        >
          View monitor
        </Link>

        {actions.map((action) => (
          <button
            key={action.status}
            type="button"
            role="menuitem"
            disabled={pendingStatus !== null}
            onClick={() => changeStatus(action.status)}
            className={`block w-full px-4 py-2 text-left text-sm disabled:cursor-wait disabled:opacity-60 ${action.className}`}
          >
            {pendingStatus === action.status ? "Updating…" : action.label}
          </button>
        ))}

        {incidentId === null && (
          <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
            Latency status is managed automatically.
          </p>
        )}

        {incidentId !== null && actions.length === 0 && (
          <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
            Resolved incidents are historical.
          </p>
        )}
      </ActionMenu>

      {error && (
        <p role="alert" className="mt-1 max-w-52 text-right text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
