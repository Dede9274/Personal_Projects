import { apiRequest } from "@/lib/api/client";
import type {
  NotificationPreferences,
  TestEmailResponse,
  UpdateNotificationPreferencesInput,
} from "@/lib/api/types";

export function getNotificationPreferences(): Promise<NotificationPreferences> {
  return apiRequest<NotificationPreferences>("/notification-settings", {
    cache: "no-store",
  });
}

export function updateNotificationPreferences(
  preferences: UpdateNotificationPreferencesInput,
): Promise<NotificationPreferences> {
  return apiRequest<NotificationPreferences>("/notification-settings", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(preferences),
  });
}

export function sendTestEmail(): Promise<TestEmailResponse> {
  return apiRequest<TestEmailResponse>(
    "/notification-settings/test-email",
    { method: "POST" },
  );
}
