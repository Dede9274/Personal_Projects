import Link from "next/link";

export default function Topbar() {
    return (
        <header className="sticky top-0 z-10 flex h-16 items-center justify-end gap-5 border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6">
            <form
                action="/monitors"
                method="get"
                role="search"
                className="relative hidden w-64 sm:block"
            >
                <label htmlFor="global-monitor-search" className="sr-only">
                    Search all monitors
                </label>
                <button
                    type="submit"
                    aria-label="Search monitors"
                    className="absolute left-1 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 transition hover:bg-white hover:text-blue-600 focus-visible:outline-2 focus-visible:outline-blue-600"
                >
                    <svg
                        aria-hidden="true"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="size-4"
                    >
                        <circle cx="11" cy="11" r="7" />
                        <path d="m20 20-3.6-3.6" />
                    </svg>
                </button>
                <input
                    id="global-monitor-search"
                    name="query"
                    type="search"
                    autoComplete="off"
                    placeholder="Search monitors..."
                    className="w-full rounded-lg bg-slate-100 py-2 pl-10 pr-4 text-sm text-slate-700 outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500"
                />
            </form>

            <Link
                href="/notifications"
                aria-label="Open notification settings"
                title="Notifications"
                className="relative flex h-9 w-9 items-center justify-center rounded-full text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
            >
                <svg
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="size-5"
                >
                    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                <span
                    aria-hidden="true"
                    className="absolute right-1 top-1 size-2.5 rounded-full bg-red-500 ring-2 ring-white"
                />
            </Link>

            <div className="h-8 border-l border-slate-200" />

            <details className="group relative">
                <summary className="flex cursor-pointer list-none items-center gap-3 rounded-lg px-1 py-1 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 [&::-webkit-details-marker]:hidden">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-800 text-sm font-medium text-white">
                        OD
                    </div>

                    <span className="hidden text-sm font-medium text-slate-800 sm:block">
                        Olti Demiri
                    </span>

                    <svg
                        aria-hidden="true"
                        viewBox="0 0 20 20"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="hidden size-4 text-slate-500 transition group-open:rotate-180 sm:block"
                    >
                        <path d="m6 8 4 4 4-4" />
                    </svg>
                    <span className="sr-only">Open account menu</span>
                </summary>

                <div className="absolute right-0 top-full z-30 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
                    <p className="text-sm font-semibold text-slate-900">
                        Account features are coming soon
                    </p>
                    <p className="mt-1 text-sm leading-5 text-slate-500">
                        Accounts and group monitoring are still a work in progress and will be available in a future update.
                    </p>
                </div>
            </details>
        </header>
    );
}
