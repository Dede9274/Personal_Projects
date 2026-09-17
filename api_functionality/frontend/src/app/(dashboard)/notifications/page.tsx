import NotificationPreferencesForm from "@/components/notifications/NotificationPreferencesForm";

export default function NotificationsPage() {
  return (
    <main className="mx-auto w-full max-w-6xl p-4 sm:p-6 lg:p-8">
      <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">Notifications</h1>
      <p className="mt-1 max-w-2xl text-base text-slate-500">
        Choose how incident alerts are delivered and configure each channel&apos;s preferences.
      </p>

      <NotificationPreferencesForm />
    </main>
  );
}
