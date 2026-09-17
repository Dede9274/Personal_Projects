import Link from "next/link";
import { notFound } from "next/navigation";

import NewMonitorForm from "@/components/monitors/new/NewMonitorForm";
import { ApiError } from "@/lib/api/client";
import { getMonitor } from "@/lib/api/monitors";
import type { Monitor } from "@/lib/api/types";

type EditMonitorPageProps = {
  params: Promise<{ id: string }>;
};

export default async function EditMonitorPage({ params }: EditMonitorPageProps) {
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
          <p className="mt-2 text-sm">{loadError}</p>
          <Link href="/monitors" className="mt-4 inline-block font-semibold text-blue-700">
            Return to monitors
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl p-4 sm:p-6 lg:p-8">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/monitors" className="hover:text-blue-600">
          Monitors
        </Link>
        <span aria-hidden="true">›</span>
        <Link href={`/monitors/${monitor.id}`} className="hover:text-blue-600">
          {monitor.name}
        </Link>
        <span aria-hidden="true">›</span>
        <span className="font-medium text-slate-700">Edit</span>
      </nav>

      <div className="mt-4">
        <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
          Edit Monitor
        </h1>
        <p className="mt-1 text-base text-slate-500">
          Update this monitor&apos;s endpoint and scheduling configuration.
        </p>
      </div>

      <NewMonitorForm monitor={monitor} />
    </main>
  );
}
