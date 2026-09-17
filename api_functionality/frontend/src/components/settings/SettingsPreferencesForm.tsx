"use client";

import { type FormEvent, useMemo, useState, useSyncExternalStore } from "react";

type SettingsValues = {
  defaultIntervalSeconds: number;
  requestTimeoutSeconds: number;
  expectedStatusCode: number;
  followRedirects: boolean;
  responseWarningThresholdMs: number;
  dashboardRefreshSeconds: number;
  timeFormat: "12-hour" | "24-hour";
};

const STORAGE_KEY = "api-checker-settings";
const SETTINGS_CHANGED_EVENT = "api-checker-settings-changed";

const DEFAULT_SETTINGS: SettingsValues = {
  defaultIntervalSeconds: 300,
  requestTimeoutSeconds: 10,
  expectedStatusCode: 200,
  followRedirects: true,
  responseWarningThresholdMs: 1_000,
  dashboardRefreshSeconds: 30,
  timeFormat: "24-hour",
};

const DEFAULT_SETTINGS_JSON = JSON.stringify(DEFAULT_SETTINGS);

const inputClasses =
  "h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function readSettingsSnapshot(): string {
  try {
    return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_SETTINGS_JSON;
  } catch {
    return DEFAULT_SETTINGS_JSON;
  }
}

function subscribeToSettings(onStoreChange: () => void): () => void {
  function handleStorage(event: StorageEvent) {
    if (event.key === STORAGE_KEY) onStoreChange();
  }

  window.addEventListener("storage", handleStorage);
  window.addEventListener(SETTINGS_CHANGED_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(SETTINGS_CHANGED_EVENT, onStoreChange);
  };
}

function numberOrDefault(
  value: unknown,
  fallback: number,
  minimum: number,
  maximum: number,
): number {
  return typeof value === "number" &&
    Number.isFinite(value) &&
    value >= minimum &&
    value <= maximum
    ? value
    : fallback;
}

function parseSettings(snapshot: string): SettingsValues {
  try {
    const parsed = JSON.parse(snapshot) as Partial<SettingsValues>;

    return {
      defaultIntervalSeconds: numberOrDefault(
        parsed.defaultIntervalSeconds,
        DEFAULT_SETTINGS.defaultIntervalSeconds,
        1,
        86_400,
      ),
      requestTimeoutSeconds: numberOrDefault(
        parsed.requestTimeoutSeconds,
        DEFAULT_SETTINGS.requestTimeoutSeconds,
        0.1,
        120,
      ),
      expectedStatusCode: numberOrDefault(
        parsed.expectedStatusCode,
        DEFAULT_SETTINGS.expectedStatusCode,
        100,
        599,
      ),
      followRedirects:
        typeof parsed.followRedirects === "boolean"
          ? parsed.followRedirects
          : DEFAULT_SETTINGS.followRedirects,
      responseWarningThresholdMs: numberOrDefault(
        parsed.responseWarningThresholdMs,
        DEFAULT_SETTINGS.responseWarningThresholdMs,
        1,
        60_000,
      ),
      dashboardRefreshSeconds: numberOrDefault(
        parsed.dashboardRefreshSeconds,
        DEFAULT_SETTINGS.dashboardRefreshSeconds,
        5,
        300,
      ),
      timeFormat:
        parsed.timeFormat === "12-hour" || parsed.timeFormat === "24-hour"
          ? parsed.timeFormat
          : DEFAULT_SETTINGS.timeFormat,
    };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export default function SettingsPreferencesForm() {
  const storedSnapshot = useSyncExternalStore(
    subscribeToSettings,
    readSettingsSnapshot,
    () => DEFAULT_SETTINGS_JSON,
  );
  const settings = useMemo(
    () => parseSettings(storedSnapshot),
    [storedSnapshot],
  );
  const [saved, setSaved] = useState(false);

  function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const nextSettings: SettingsValues = {
      defaultIntervalSeconds: Number(form.get("default_interval_seconds")),
      requestTimeoutSeconds: Number(form.get("request_timeout_seconds")),
      expectedStatusCode: Number(form.get("expected_status_code")),
      followRedirects: form.has("follow_redirects"),
      responseWarningThresholdMs: Number(
        form.get("response_warning_threshold_ms"),
      ),
      dashboardRefreshSeconds: Number(
        form.get("dashboard_refresh_seconds"),
      ),
      timeFormat:
        form.get("time_format") === "12-hour" ? "12-hour" : "24-hour",
    };

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSettings));
    window.dispatchEvent(new Event(SETTINGS_CHANGED_EVENT));
    setSaved(true);
  }

  return (
    <form
      key={storedSnapshot}
      onSubmit={saveSettings}
      onChange={() => setSaved(false)}
      className="mt-6 space-y-5"
    >
      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-200 px-5 py-5 sm:px-6">
          <h2 className="text-lg font-bold text-slate-950">
            Monitoring Defaults
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Configure the starting values shown when setting up monitoring.
          </p>
        </header>

        <div className="divide-y divide-slate-100 px-5 sm:px-6">
          <SettingRow
            label="Default check interval"
            description="How often a monitor should run by default."
          >
            <select
              name="default_interval_seconds"
              defaultValue={settings.defaultIntervalSeconds}
              className={inputClasses}
            >
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
              <option value={600}>10 minutes</option>
              <option value={1_800}>30 minutes</option>
            </select>
          </SettingRow>

          <SettingRow
            label="Request timeout"
            description="Maximum time to wait for a response."
          >
            <div className="relative">
              <input
                name="request_timeout_seconds"
                type="number"
                required
                min={0.1}
                max={120}
                step={0.1}
                defaultValue={settings.requestTimeoutSeconds}
                className={`${inputClasses} pr-20`}
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                seconds
              </span>
            </div>
          </SettingRow>

          <SettingRow
            label="Expected status code"
            description="The HTTP status considered successful."
          >
            <input
              name="expected_status_code"
              type="number"
              required
              min={100}
              max={599}
              defaultValue={settings.expectedStatusCode}
              className={inputClasses}
            />
          </SettingRow>

          <SettingRow
            label="Follow redirects"
            description="Allow checks to follow HTTP redirect responses."
          >
            <label className="inline-flex cursor-pointer items-center gap-3">
              <input
                name="follow_redirects"
                type="checkbox"
                defaultChecked={settings.followRedirects}
                className="peer sr-only"
              />
              <span className="relative h-7 w-12 rounded-full bg-slate-300 transition after:absolute after:left-1 after:top-1 after:size-5 after:rounded-full after:bg-white after:shadow-sm after:transition peer-checked:bg-blue-600 peer-checked:after:translate-x-5 peer-focus-visible:ring-2 peer-focus-visible:ring-blue-500 peer-focus-visible:ring-offset-2" />
              <span className="text-sm font-semibold text-slate-700">
                Enabled
              </span>
            </label>
          </SettingRow>

          <SettingRow
            label="Response warning threshold"
            description="Mark responses above this duration as slow."
          >
            <div className="relative">
              <input
                name="response_warning_threshold_ms"
                type="number"
                required
                min={1}
                max={60_000}
                defaultValue={settings.responseWarningThresholdMs}
                className={`${inputClasses} pr-12`}
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                ms
              </span>
            </div>
          </SettingRow>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-200 px-5 py-5 sm:px-6">
          <h2 className="text-lg font-bold text-slate-950">Appearance</h2>
          <p className="mt-1 text-sm text-slate-500">
            Choose how frequently information refreshes and how time is shown.
          </p>
        </header>

        <div className="divide-y divide-slate-100 px-5 sm:px-6">
          <SettingRow
            label="Dashboard refresh"
            description="How often dashboard information should refresh."
          >
            <select
              name="dashboard_refresh_seconds"
              defaultValue={settings.dashboardRefreshSeconds}
              className={inputClasses}
            >
              <option value={15}>15 seconds</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={120}>2 minutes</option>
            </select>
          </SettingRow>

          <SettingRow
            label="Time format"
            description="Choose between a 12-hour and 24-hour clock."
          >
            <select
              name="time_format"
              defaultValue={settings.timeFormat}
              className={inputClasses}
            >
              <option value="24-hour">24 hour</option>
              <option value="12-hour">12 hour</option>
            </select>
          </SettingRow>
        </div>
      </section>

      {saved && (
        <p
          role="status"
          className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
        >
          Settings saved for this browser.
        </p>
      )}

      <footer className="flex justify-end gap-3">
        <button
          type="reset"
          onClick={() => setSaved(false)}
          className="h-11 rounded-lg border border-slate-200 bg-white px-6 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Save Settings
        </button>
      </footer>
    </form>
  );
}

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-3 py-5 md:grid-cols-[minmax(0,1fr)_minmax(220px,320px)] md:items-center md:gap-8">
      <div>
        <p className="text-sm font-semibold text-slate-900">{label}</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>
      </div>
      <div>{children}</div>
    </div>
  );
}
