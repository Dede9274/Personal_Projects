"use client";

import { type FormEvent, useMemo, useState } from "react";

import {
  sendTestEmail,
  updateNotificationPreferences,
} from "@/lib/api/notifications";
import type {
  NotificationPreferences,
  UpdateNotificationPreferencesInput,
} from "@/lib/api/types";

type NotificationPreferencesFormProps = {
  initialPreferences: NotificationPreferences;
};

type Feedback = {
  tone: "success" | "error";
  message: string;
} | null;

type NotificationToggleProps = {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
};

const inputClasses =
  "mt-2 h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400";

function NotificationToggle({
  checked,
  label,
  onChange,
}: NotificationToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 cursor-pointer rounded-full transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${
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

function editablePreferences(
  preferences: NotificationPreferences,
): UpdateNotificationPreferencesInput {
  return {
    email_enabled: preferences.email_enabled,
    email_recipients: preferences.email_recipients,
    email_timeout_seconds: preferences.email_timeout_seconds,
    webhook_enabled: preferences.webhook_enabled,
    webhook_url: preferences.webhook_url,
    webhook_timeout_seconds: preferences.webhook_timeout_seconds,
    notify_incident_opened: preferences.notify_incident_opened,
  };
}

export default function NotificationPreferencesForm({
  initialPreferences,
}: NotificationPreferencesFormProps) {
  const [savedPreferences, setSavedPreferences] = useState(initialPreferences);
  const [preferences, setPreferences] = useState(
    editablePreferences(initialPreferences),
  );
  const [recipientInput, setRecipientInput] = useState(
    initialPreferences.email_recipients.join(", "),
  );
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const isDirty = useMemo(
    () =>
      JSON.stringify(preferences) !==
        JSON.stringify(editablePreferences(savedPreferences)) ||
      recipientInput !== savedPreferences.email_recipients.join(", "),
    [preferences, recipientInput, savedPreferences],
  );

  function updatePreference<K extends keyof UpdateNotificationPreferencesInput>(
    key: K,
    value: UpdateNotificationPreferencesInput[K],
  ) {
    setPreferences((current) => ({ ...current, [key]: value }));
    setFeedback(null);
  }

  function resetForm() {
    setPreferences(editablePreferences(savedPreferences));
    setRecipientInput(savedPreferences.email_recipients.join(", "));
    setFeedback(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    const emailRecipients = recipientInput
      .split(",")
      .map((address) => address.trim())
      .filter(Boolean);

    try {
      const saved = await updateNotificationPreferences({
        ...preferences,
        email_recipients: emailRecipients,
        webhook_url: preferences.webhook_url?.trim() || null,
      });
      setSavedPreferences(saved);
      setPreferences(editablePreferences(saved));
      setRecipientInput(saved.email_recipients.join(", "));
      setFeedback({
        tone: "success",
        message: "Notification preferences saved and active.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "Notification preferences could not be saved.",
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleTestEmail() {
    setIsTesting(true);
    setFeedback(null);

    try {
      const result = await sendTestEmail();
      setFeedback({
        tone: "success",
        message: `${result.message}: ${result.recipients.join(", ")}`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message:
          error instanceof Error
            ? error.message
            : "The test email could not be sent.",
      });
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 space-y-5">
      <section aria-labelledby="channels-heading">
        <div className="mb-4">
          <h2 id="channels-heading" className="text-lg font-bold text-slate-950">
            Notification channels
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Preferences are stored in PostgreSQL and read by the notification
            worker for every delivery.
          </p>
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-2">
          <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
              <div className="flex items-center gap-4">
                <span
                  aria-hidden="true"
                  className="flex size-12 items-center justify-center rounded-xl bg-blue-100 text-xl font-bold text-blue-600"
                >
                  @
                </span>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-slate-950">
                      Email notifications
                    </h3>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        savedPreferences.smtp_configured
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {savedPreferences.smtp_configured
                        ? "SMTP ready"
                        : "SMTP setup required"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-slate-500">
                    Send an email when an incident opens.
                  </p>
                </div>
              </div>
              <NotificationToggle
                checked={preferences.email_enabled}
                label="Enable email notifications"
                onChange={(enabled) =>
                  updatePreference("email_enabled", enabled)
                }
              />
            </header>

            <div className="border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs leading-5 text-slate-600 sm:px-6">
              {savedPreferences.smtp_configured ? (
                <p>
                  Sending from {savedPreferences.smtp_from_email} through{" "}
                  {savedPreferences.smtp_host}:{savedPreferences.smtp_port} ({
                    savedPreferences.smtp_security
                  }). Credentials remain server-side.
                </p>
              ) : (
                <p>
                  {savedPreferences.smtp_configuration_error}. Add SMTP values
                  to <code>.env</code>, then recreate the backend services.
                </p>
              )}
            </div>

            <fieldset
              disabled={!preferences.email_enabled}
              className="space-y-5 px-5 py-6 disabled:opacity-60 sm:px-6"
            >
              <label className="block text-sm font-medium text-slate-700">
                Recipient email
                <input
                  name="alert_email_to"
                  type="email"
                  multiple
                  required={preferences.email_enabled}
                  value={recipientInput}
                  onChange={(event) => {
                    setRecipientInput(event.target.value);
                    setFeedback(null);
                  }}
                  placeholder="alerts@example.com"
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
                    required={preferences.email_enabled}
                    min={1}
                    max={120}
                    value={preferences.email_timeout_seconds}
                    onChange={(event) =>
                      updatePreference(
                        "email_timeout_seconds",
                        Number(event.target.value),
                      )
                    }
                    className={`${inputClasses} pr-20`}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                    seconds
                  </span>
                </div>
              </label>

              <button
                type="button"
                onClick={handleTestEmail}
                disabled={
                  !savedPreferences.smtp_configured ||
                  !savedPreferences.email_enabled ||
                  isDirty ||
                  isTesting
                }
                className="h-10 rounded-lg border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isTesting ? "Sending test…" : "Send test email"}
              </button>
              {isDirty && preferences.email_enabled && (
                <p className="text-xs text-slate-500">
                  Save your changes before sending a test email.
                </p>
              )}
            </fieldset>
          </article>

          <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
              <div className="flex items-center gap-4">
                <span
                  aria-hidden="true"
                  className="flex size-12 items-center justify-center rounded-xl bg-violet-100 text-xl font-bold text-violet-600"
                >
                  ↗
                </span>
                <div>
                  <h3 className="font-bold text-slate-950">
                    Webhook notifications
                  </h3>
                  <p className="mt-0.5 text-sm text-slate-500">
                    Send signed incident JSON to another service.
                  </p>
                </div>
              </div>
              <NotificationToggle
                checked={preferences.webhook_enabled}
                label="Enable webhook notifications"
                onChange={(enabled) =>
                  updatePreference("webhook_enabled", enabled)
                }
              />
            </header>

            <fieldset
              disabled={!preferences.webhook_enabled}
              className="space-y-5 px-5 py-6 disabled:opacity-60 sm:px-6"
            >
              <label className="block text-sm font-medium text-slate-700">
                Webhook URL
                <input
                  name="alert_webhook_url"
                  type="url"
                  required={preferences.webhook_enabled}
                  value={preferences.webhook_url ?? ""}
                  onChange={(event) =>
                    updatePreference("webhook_url", event.target.value)
                  }
                  placeholder="https://example.com/webhooks/uptime"
                  className={inputClasses}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Webhook request timeout
                <div className="relative">
                  <input
                    name="webhook_timeout_seconds"
                    type="number"
                    required={preferences.webhook_enabled}
                    min={1}
                    max={120}
                    value={preferences.webhook_timeout_seconds}
                    onChange={(event) =>
                      updatePreference(
                        "webhook_timeout_seconds",
                        Number(event.target.value),
                      )
                    }
                    className={`${inputClasses} pr-20`}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 mt-1 -translate-y-1/2 text-sm text-slate-400">
                    seconds
                  </span>
                </div>
              </label>
            </fieldset>
          </article>
        </div>
      </section>

      <section
        aria-labelledby="events-heading"
        className="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <header className="border-b border-slate-200 px-5 py-5 sm:px-6">
          <h2 id="events-heading" className="text-lg font-bold text-slate-950">
            Notification events
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            An incident opens after three consecutive failed checks.
          </p>
        </header>

        <div className="px-5 py-5 sm:px-6">
          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-4 hover:bg-slate-50">
            <input
              name="notify_incident_opened"
              type="checkbox"
              checked={preferences.notify_incident_opened}
              onChange={(event) =>
                updatePreference(
                  "notify_incident_opened",
                  event.target.checked,
                )
              }
              className="mt-0.5 size-4 accent-blue-600"
            />
            <span>
              <span className="block text-sm font-semibold text-slate-900">
                Incident opened
              </span>
              <span className="mt-1 block text-sm text-slate-500">
                Notify each enabled channel once per incident, with independent
                retries and duplicate protection.
              </span>
            </span>
          </label>
        </div>
      </section>

      {feedback && (
        <div
          role={feedback.tone === "error" ? "alert" : "status"}
          className={`rounded-lg border px-4 py-3 text-sm ${
            feedback.tone === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {feedback.message}
        </div>
      )}

      <footer className="flex justify-end gap-3">
        <button
          type="button"
          onClick={resetForm}
          disabled={!isDirty || isSaving}
          className="h-11 rounded-lg border border-slate-200 bg-white px-6 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Reset
        </button>
        <button
          type="submit"
          disabled={!isDirty || isSaving}
          className="h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          {isSaving ? "Saving…" : "Save Preferences"}
        </button>
      </footer>
    </form>
  );
}
