"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const selectClasses =
  "h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

type MonitorToolbarProps = {
  query?: string;
  status?: string;
  sort?: string;
};

export default function MonitorToolbar({
  query,
  status = "all",
  sort = "name-asc",
}: MonitorToolbarProps) {
  const initialQuery = query ?? "";
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (searchQuery.trim() === initialQuery.trim()) return;

    const timeoutId = window.setTimeout(() => {
      searchInputRef.current?.form?.requestSubmit();
    }, 400);

    return () => window.clearTimeout(timeoutId);
  }, [initialQuery, searchQuery]);

  return (
    <form
      action="/monitors"
      method="get"
      className="mt-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-2 xl:grid-cols-[minmax(320px,1fr)_168px_180px_auto_auto] xl:items-end"
    >
      <label className="relative md:col-span-2 xl:col-span-1">
        <span className="sr-only">Search monitors</span>
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-slate-500"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.6-3.6" />
        </svg>
        <input
          ref={searchInputRef}
          name="query"
          type="search"
          autoComplete="off"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search monitors by name, URL, or purpose..."
          className="h-11 w-full rounded-lg border border-slate-200 bg-white pl-10 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">
          Status
        </span>
        <select name="status" defaultValue={status} className={selectClasses}>
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
        </select>
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">
          Sort by
        </span>
        <select name="sort" defaultValue={sort} className={selectClasses}>
          <option value="name-asc">Name (A-Z)</option>
          <option value="name-desc">Name (Z-A)</option>
          <option value="interval-asc">Shortest Interval</option>
          <option value="interval-desc">Longest Interval</option>
          <option value="newest">Newest First</option>
        </select>
      </label>

      <button
        type="submit"
        className="flex h-11 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 px-5 text-sm font-semibold whitespace-nowrap text-blue-700 transition hover:bg-blue-100"
      >
        Apply Filters
      </button>

      <Link
        href="/monitors/new"
        className="flex h-11 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 text-sm font-semibold whitespace-nowrap text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 md:col-span-2 xl:col-span-1"
      >
        <span aria-hidden="true" className="text-xl font-light leading-none">
          +
        </span>
        Add Monitor
      </Link>
    </form>
  );
}
