"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { runMonitorCheck, updateMonitor } from "@/lib/api/monitors";

type MonitorHeaderActionsProps = {
  monitorId: number;
  isActive: boolean;
};

type CheckFeedback = {
  status: "queued" | "already_outstanding";
  message: string;
};

export default function MonitorHeaderActions({
  monitorId,
  isActive,
}: MonitorHeaderActionsProps) {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);
  const [isQueueingCheck, setIsQueueingCheck] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [checkFeedback, setCheckFeedback] = useState<CheckFeedback | null>(null);

  async function toggleActiveState() {
    setIsSaving(true);
    setErrorMessage(null);
    setCheckFeedback(null);

    try {
      await updateMonitor(monitorId, { is_active: !isActive });
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "The monitor could not be updated.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function queueManualCheck() {
    if (!isActive || isQueueingCheck) return;

    setIsQueueingCheck(true);
    setErrorMessage(null);
    setCheckFeedback(null);

    try {
      const response = await runMonitorCheck(monitorId);

      setCheckFeedback({
        status: response.status,
        message:
          response.status === "queued"
            ? "Check queued. The result will appear below when the worker finishes."
            : "A check is already queued or running, so no duplicate was added.",
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The manual check could not be queued.",
      );
    } finally {
      setIsQueueingCheck(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        <Link
          href={`/monitors/${monitorId}/edit`}
          className="flex h-11 items-center rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          ✎&nbsp; Edit
        </Link>
        <button
          type="button"
          disabled={isSaving || isQueueingCheck}
          onClick={toggleActiveState}
          className="h-11 rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-wait disabled:text-slate-400"
        >
          {isSaving ? "Saving..." : isActive ? "Ⅱ  Pause" : "▶  Resume"}
        </button>
        <button
          type="button"
          disabled={!isActive || isSaving || isQueueingCheck}
          onClick={queueManualCheck}
          title={
            isActive
              ? "Queue an additional check without changing the interval schedule"
              : "Resume this monitor before running a manual check"
          }
          className="h-11 rounded-lg bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
        >
          {isQueueingCheck ? "Queueing…" : "▶  Run Check"}
        </button>
      </div>
      {checkFeedback && (
        <p
          role="status"
          aria-live="polite"
          className={`mt-2 text-sm ${
            checkFeedback.status === "queued"
              ? "text-emerald-700"
              : "text-blue-700"
          }`}
        >
          {checkFeedback.message}
        </p>
      )}
      {errorMessage && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
