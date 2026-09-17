"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

const DASHBOARD_REFRESH_INTERVAL_MS = 15_000;

export default function DashboardAutoRefresh() {
  const router = useRouter();

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        router.refresh();
      }
    }, DASHBOARD_REFRESH_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [router]);

  return null;
}
