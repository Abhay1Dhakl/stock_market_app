import { API_BASE_URL } from "@/lib/api";
import type { TokenResponse } from "@/types";

type TelemetryPayload = {
  event_type: string;
  page_path?: string;
  company_id?: number;
  article_id?: number;
  metadata?: Record<string, unknown>;
  notes?: string;
};

export async function trackEvent(session: TokenResponse | null, payload: TelemetryPayload): Promise<void> {
  if (!session) {
    return;
  }

  try {
    await fetch(`${API_BASE_URL}/telemetry/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
  } catch {
    // Telemetry should never block the primary UX.
  }
}
