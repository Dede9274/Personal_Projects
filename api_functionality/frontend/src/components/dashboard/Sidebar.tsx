"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();
  const linkClass = (href: string) => {
    const active =
      href === "/"
        ? pathname === "/"
        : pathname === href || pathname.startsWith(`${href}/`);

    return active
      ? "rounded-lg bg-slate-700 px-4 py-3 text-[15px] font-medium text-white shadow-sm"
      : "rounded-lg px-4 py-3 text-[15px] font-medium text-slate-300 hover:bg-slate-800 hover:text-white";
  };

  return (
    <aside className="hidden h-screen w-60 shrink-0 flex-col bg-[#111c2d] px-4 py-6 text-slate-200 lg:sticky lg:top-0 lg:flex">
      <div className="px-3">
        <p className="text-xl font-bold text-white">API Checker</p>
        <p className="mt-1 text-xs text-slate-400">Monitor. Verify. Stay online.</p>
      </div>
      <nav className="mt-10 flex flex-col gap-2">
        <Link href="/" className={linkClass("/")}>Dashboard</Link>
        <Link href="/monitors" className={linkClass("/monitors")}>Monitors</Link>
        <Link href="/incidents" className={linkClass("/incidents")}>Incidents</Link>
        <Link href="/notifications" className={linkClass("/notifications")}>Notifications</Link>
        <Link href="/settings" className={linkClass("/settings")}>Settings</Link>
      </nav>

      <div className="mt-auto space-y-1 border-t border-slate-700 pt-5 text-sm text-slate-300">
        <p className="rounded-lg px-4 py-2">Documentation</p>
        <p className="rounded-lg px-4 py-2">Help</p>
      </div>
    </aside>
  );
}
