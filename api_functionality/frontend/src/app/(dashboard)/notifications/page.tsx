import NotificationPreferencesForm from "@/components/notifications/NotificationPreferencesForm";
import { getNotificationPreferences } from "@/lib/api/notifications";

export default async function NotificationsPage() {
  let preferences = null;
  let errorMessage = null;

  try {
    preferences = await getNotificationPreferences();
  } catch (error) {
    errorMessage =
      error instanceof Error
        ? error.message
        : "Notification settings could not be loaded.";
  }

  return (
    <main className="mx-auto w-full max-w-6xl p-4 sm:p-6 lg:p-8">
      <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">
        Notifications
      </h1>
      <p className="mt-1 max-w-2xl text-base text-slate-500">
        Configure incident delivery, verify SMTP, and send a test email.
      </p>

      {preferences ? (
        <NotificationPreferencesForm initialPreferences={preferences} />
      ) : (
        <div
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700"
        >
          {errorMessage}
        </div>
      )}
    </main>
  );
}
