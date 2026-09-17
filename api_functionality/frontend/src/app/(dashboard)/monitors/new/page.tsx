import Link from "next/link";

import NewMonitorForm from "@/components/monitors/new/NewMonitorForm";

export default function NewMonitorPage() {
  return (
    <main className="mx-auto w-full max-w-5xl p-4 sm:p-6 lg:p-8">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/monitors" className="transition hover:text-blue-600">
          Monitors
        </Link>
        <span aria-hidden="true">›</span>
        <span className="font-medium text-slate-700">Add new monitor</span>
      </nav>

      <div className="mt-4">
        <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
          Add a New Monitor
        </h1>
        <p className="mt-1 text-base text-slate-500">
          Add an API endpoint and define how the monitoring system should check it.
        </p>
      </div>

      <NewMonitorForm />
    </main>
  );
}
