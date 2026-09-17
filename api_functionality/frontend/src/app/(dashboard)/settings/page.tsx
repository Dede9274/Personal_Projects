import SettingsPreferencesForm from "@/components/settings/SettingsPreferencesForm";

export default function SettingsPage() {
  return (
    <main className="mx-auto w-full max-w-5xl p-4 sm:p-6 lg:p-8">
      <h1 className="text-[32px] leading-tight font-bold tracking-tight text-slate-900 sm:text-[34px]">Settings</h1>
      <p className="mt-1 text-base text-slate-500">
        Manage monitoring defaults and dashboard preferences.
      </p>

      <SettingsPreferencesForm />
    </main>
  );
}
