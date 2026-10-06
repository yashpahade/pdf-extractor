export type ComponentStatus = "ok" | "error";

export interface ReadinessResponse {
  status: ComponentStatus;
  checks: {
    database: ComponentStatus;
    vector_store: ComponentStatus;
  };
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchReadiness(
  signal: AbortSignal,
): Promise<ReadinessResponse> {
  const response = await fetch(`${apiBaseUrl}/api/health/ready`, { signal });

  if (!response.ok) {
    throw new Error(`API readiness check failed with HTTP ${response.status}`);
  }

  return (await response.json()) as ReadinessResponse;
}
