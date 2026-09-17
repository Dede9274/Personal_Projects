"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const selectClasses =
  "h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

type IncidentSearchBarProps = {
  query: string;
  status: string;
  severity: string;
  range: string;
  sort: string;
  searchOptions: string[];
};

export default function IncidentSearchBar({
  query,
  status,
  severity,
  range,
  sort,
  searchOptions,
}: IncidentSearchBarProps) {
  const [searchQuery, setSearchQuery] = useState(query);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (searchQuery.trim() === query.trim()) return;

    const timeoutId = window.setTimeout(() => {
      searchInputRef.current?.form?.requestSubmit();
    }, 400);

    return () => window.clearTimeout(timeoutId);
  }, [query, searchQuery]);

  return (
    <form
      action="/incidents"
      method="get"
      className="mt-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-2 xl:grid-cols-[minmax(280px,1fr)_150px_140px_160px_160px_auto_auto] xl:items-end"
    >
      <label className="relative md:col-span-2 xl:col-span-1">
        <span className="sr-only">Search incidents</span>
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
          list="incident-search-options"
          autoComplete="off"
          placeholder="Search by incident or monitor..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          className="h-11 w-full rounded-lg border border-slate-200 bg-white pl-10 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
        <datalist id="incident-search-options">
          {searchOptions.map((option) => (
            <option key={option} value={option} />
          ))}
        </datalist>
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">
          Status
        </span>
        <select name="status" defaultValue={status} className={selectClasses}>
          <option value="all">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
        </select>
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">Severity</span>
        <select name="severity" defaultValue={severity} className={selectClasses}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">Date range</span>
        <select name="range" defaultValue={range} className={selectClasses}>
          <option value="24-hours">Last 24 hours</option>
          <option value="7-days">Last 7 days</option>
          <option value="30-days">Last 30 days</option>
          <option value="90-days">Last 90 days</option>
          <option value="all">All time</option>
        </select>
      </label>

      <label className="block min-w-0">
        <span className="mb-1 block text-xs font-medium text-slate-500">Sort by</span>
        <select name="sort" defaultValue={sort} className={selectClasses}>
          <option value="started-desc">Newest first</option>
          <option value="started-asc">Oldest first</option>
          <option value="severity">Severity</option>
          <option value="duration">Longest duration</option>
        </select>
      </label>

      <button
        type="submit"
        className="flex h-11 items-center justify-center rounded-lg bg-blue-600 px-5 text-sm font-semibold whitespace-nowrap text-white transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        Apply
      </button>

      <Link
        href="/incidents"
        className="flex h-11 items-center justify-center rounded-lg px-5 text-sm font-semibold whitespace-nowrap text-blue-600 transition hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 md:col-span-2 xl:col-span-1"
      >
        Clear Filters
      </Link>
    </form>
  );
}
