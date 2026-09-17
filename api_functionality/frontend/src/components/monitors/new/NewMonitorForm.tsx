"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createMonitor, updateMonitor } from "@/lib/api/monitors";
import type { Monitor } from "@/lib/api/types";

const inputClasses =
  "mt-2 h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

type MonitorFormProps = {
  monitor?: Monitor;
};

export default function NewMonitorForm({ monitor }: MonitorFormProps) {
  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isEditing = monitor !== undefined;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const values = {
      name: String(formData.get("name")),
      url: String(formData.get("url")),
      purpose: String(formData.get("purpose")),
      interval_seconds: Number(formData.get("interval_seconds")),
      timeout_seconds: Number(formData.get("timeout_seconds")),
      expected_status_code: Number(formData.get("expected_status_code")),
      is_active: monitor?.is_active ?? true,
    };

    try {
      const savedMonitor = monitor
        ? await updateMonitor(monitor.id, values)
        : await createMonitor(values);

      router.push(`/monitors/${savedMonitor.id}`);
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "The monitor could not be saved.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      onChange={() => setErrorMessage(null)}
      className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <header className="border-b border-slate-200 px-5 py-5 sm:px-7">
        <h2 className="text-lg font-bold text-slate-950">
          {isEditing ? "Edit monitor details" : "Monitor details"}
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Enter the endpoint and rules the monitoring worker should use.
        </p>
      </header>

      <div className="space-y-8 px-5 py-6 sm:px-7">
        <section aria-labelledby="basic-information-heading">
          <h3 id="basic-information-heading" className="font-semibold text-slate-950">
            Basic information
          </h3>

          <div className="mt-4 grid gap-5 md:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Monitor name
              <input
                name="name"
                type="text"
                required
                maxLength={100}
                defaultValue={monitor?.name}
                placeholder="Payments API"
                className={inputClasses}
              />
              <span className="mt-1.5 block text-xs font-normal text-slate-500">
                A clear name that identifies this service.
              </span>
            </label>

            <label className="block text-sm font-medium text-slate-700">
              URL
              <input
                name="url"
                type="url"
                required
                defaultValue={monitor?.url}
                placeholder="https://api.example.com/health"
                className={inputClasses}
              />
              <span className="mt-1.5 block text-xs font-normal text-slate-500">
                Include the complete address beginning with http:// or https://.
              </span>
            </label>
          </div>

          <label className="mt-5 block text-sm font-medium text-slate-700">
            API&apos;s purpose
            <textarea
              name="purpose"
              required
              maxLength={500}
              rows={4}
              defaultValue={monitor?.purpose}
              placeholder="Describe what this API does and why it is important..."
              className="mt-2 w-full resize-y rounded-lg border border-slate-200 bg-white px-3 py-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
            <span className="mt-1.5 block text-xs font-normal text-slate-500">
              This description will help identify the monitor on its details page.
            </span>
          </label>
        </section>

        <section aria-labelledby="check-settings-heading" className="border-t border-slate-200 pt-7">
          <h3 id="check-settings-heading" className="font-semibold text-slate-950">
            Check settings
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Configure how frequently the endpoint is checked and what counts as success.
          </p>

          <div className="mt-4 grid gap-5 md:grid-cols-3">
            <label className="block text-sm font-medium text-slate-700">
              Check interval
              <div className="relative">
                <input
                  name="interval_seconds"
                  type="number"
                  required
                  min={1}
                  defaultValue={monitor?.interval_seconds ?? 300}
                  className={`${inputClasses} pr-20`}
                />
                <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                  seconds
                </span>
              </div>
              <span className="mt-1.5 block text-xs font-normal text-slate-500">
                300 seconds equals 5 minutes.
              </span>
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Timeout
              <div className="relative">
                <input
                  name="timeout_seconds"
                  type="number"
                  required
                  min={0.1}
                  step={0.1}
                  defaultValue={monitor?.timeout_seconds ?? 10}
                  className={`${inputClasses} pr-20`}
                />
                <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                  seconds
                </span>
              </div>
              <span className="mt-1.5 block text-xs font-normal text-slate-500">
                Stop waiting after this duration.
              </span>
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Expected status code
              <input
                name="expected_status_code"
                type="number"
                required
                min={100}
                max={599}
                defaultValue={monitor?.expected_status_code ?? 200}
                className={inputClasses}
              />
              <span className="mt-1.5 block text-xs font-normal text-slate-500">
                A different response code counts as a failed check.
              </span>
            </label>
          </div>
        </section>

        {errorMessage && (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}
      </div>

      <footer className="flex flex-col-reverse gap-3 border-t border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:justify-end sm:px-7">
        <Link
          href={monitor ? `/monitors/${monitor.id}` : "/monitors"}
          className="flex h-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
        >
          Cancel
        </Link>
        <button
          type="submit"
          disabled={isSubmitting}
          className="h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-wait disabled:bg-blue-400"
        >
          {isSubmitting
            ? "Saving..."
            : isEditing
              ? "Save Changes"
              : "Create Monitor"}
        </button>
      </footer>
    </form>
  );
}
