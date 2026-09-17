"use client";

import { type FormEvent, useState } from "react";

type NotificationToggleProps = {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
};

const inputClasses =
  "mt-2 h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400";

function NotificationToggle({ checked, label, onChange }: NotificationToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 rounded-full transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${
        checked ? "bg-blue-600" : "bg-slate-300"
      }`}
    >
      <span
        aria-hidden="true"
        className={`absolute top-1 size-5 rounded-full bg-white shadow-sm transition ${
          checked ? "left-6" : "left-1"
        }`}
      />
    </button>
  );
}

export default function NotificationPreferencesForm() {
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [saved, setSaved] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(true);
  }

  function changeEmailEnabled(enabled: boolean) {
    setEmailEnabled(enabled);
    setSaved(false);
  }

  function changeWebhookEnabled(enabled: boolean) {
    setWebhookEnabled(enabled);
    setSaved(false);
  }

  return (
    <form
      onSubmit={handleSubmit}
      onChange={() => setSaved(false)}
      className="mt-6 space-y-5"
    >
      <section aria-labelledby="channels-heading">
        <div className="mb-4">
          <h2 id="channels-heading" className="text-lg font-bold text-slate-950">
            Notification channels
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Choose where incident alerts should be delivered.
          </p>
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-2">
          <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
              <div className="flex items-center gap-4">
                <span aria-hidden="true" className="flex size-12 items-center justify-center rounded-xl bg-blue-100 text-xl font-bold text-blue-600">
                  @
                </span>
                <div>
                  <h3 className="font-bold text-slate-950">Email notifications</h3>
                  <p className="mt-0.5 text-sm text-slate-500">
                    Send incident alerts to an inbox.
                  </p>
                </div>
              </div>
              <NotificationToggle
                checked={emailEnabled}
                label="Enable email notifications"
                onChange={changeEmailEnabled}
              />
            </header>

            <fieldset disabled={!emailEnabled} className="space-y-5 px-5 py-6 disabled:opacity-60 sm:px-6">
              <label className="block text-sm font-medium text-slate-700">
                Recipient email
                <input
                  name="alert_email_to"
                  type="email"
                  multiple
                  required={emailEnabled}
                  defaultValue="owner@example.com"
                  placeholder="owner@example.com"
                  className={inputClasses}
                />
                <span className="mt-1.5 block text-xs font-normal text-slate-500">
                  Separate multiple addresses with commas.
                </span>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Email request timeout
                <div className="relative">
                  <input
                    name="smtp_timeout_seconds"
                    type="number"
                    required={emailEnabled}
                    min={1}
                    max={120}
                    defaultValue={10}
                    className={`${inputClasses} pr-20`}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                    seconds
                  </span>
                </div>
                <span className="mt-1.5 block text-xs font-normal text-slate-500">
                  Maximum time allowed for the email server to respond.
                </span>
              </label>
            </fieldset>
          </article>

          <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
              <div className="flex items-center gap-4">
                <span aria-hidden="true" className="flex size-12 items-center justify-center rounded-xl bg-violet-100 text-xl font-bold text-violet-600">
                  ↗
                </span>
                <div>
                  <h3 className="font-bold text-slate-950">Webhook notifications</h3>
                  <p className="mt-0.5 text-sm text-slate-500">
                    Send incident data to another service.
                  </p>
                </div>
              </div>
              <NotificationToggle
                checked={webhookEnabled}
                label="Enable webhook notifications"
                onChange={changeWebhookEnabled}
              />
            </header>

            <fieldset disabled={!webhookEnabled} className="space-y-5 px-5 py-6 disabled:opacity-60 sm:px-6">
              <label className="block text-sm font-medium text-slate-700">
                Webhook URL
                <input
                  name="alert_webhook_url"
                  type="url"
                  required={webhookEnabled}
                  placeholder="https://example.com/webhooks/uptime"
                  className={inputClasses}
                />
                <span className="mt-1.5 block text-xs font-normal text-slate-500">
                  Incident details will be sent as a JSON request.
                </span>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Webhook request timeout
                <div className="relative">
                  <input
                    name="webhook_timeout_seconds"
                    type="number"
                    required={webhookEnabled}
                    min={1}
                    max={120}
                    defaultValue={10}
                    className={`${inputClasses} pr-20`}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                    seconds
                  </span>
                </div>
                <span className="mt-1.5 block text-xs font-normal text-slate-500">
                  Maximum time allowed for the webhook server to respond.
                </span>
              </label>
            </fieldset>
          </article>
        </div>
      </section>

      <section aria-labelledby="events-heading" className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-200 px-5 py-5 sm:px-6">
          <h2 id="events-heading" className="text-lg font-bold text-slate-950">
            Notification events
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Select which monitoring events should create a notification.
          </p>
        </header>

        <div className="px-5 py-5 sm:px-6">
          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-4 hover:bg-slate-50">
            <input
              name="notify_incident_opened"
              type="checkbox"
              defaultChecked
              className="mt-0.5 size-4 accent-blue-600"
            />
            <span>
              <span className="block text-sm font-semibold text-slate-900">
                Incident opened
              </span>
              <span className="mt-1 block text-sm text-slate-500">
                Notify enabled channels after a monitor reaches the configured failure threshold.
              </span>
            </span>
          </label>
        </div>
      </section>

      {saved && (
        <div role="status" className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          The preferences are valid. Backend persistence must be connected before these changes affect notification workers.
        </div>
      )}

      <footer className="flex justify-end">
        <button
          type="submit"
          className="h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Save Preferences
        </button>
      </footer>
    </form>
  );
}
