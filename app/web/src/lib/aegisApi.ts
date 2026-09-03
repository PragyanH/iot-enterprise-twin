export type FleetDeviceResponse = {
  id: string;
  name: string;
  sector: string;
  source: "mock" | "pi";
  source_mode: string;
  sensor: string;
  status: string;
  trust: number;
  state: string;
  attack_type: string;
  confidence: number;
  updated_at: string;
  active_incident_id?: string | null;
};

export type AegisDeviceState = FleetDeviceResponse & {
  risk: number;
  current_features: Record<string, number>;
  baseline_features: Record<string, number>;
  reconstruction_error: number;
  latent_uncertainty: number;
  jsd: number;
  rule_risk: number;
  classifier_risk: number;
  vae_risk: number;
  baseline_risk: number;
  attention_weights: number[];
  top_anomalies: Array<{ feature: string; score: number; direction: string }>;
  detection_mode: string;
  classification: {
    type: string;
    known: boolean;
    mitre_status: string;
    mitre: { technique_id: string; technique_name: string; tactic: string } | null;
  };
  recovery_progress: {
    clean_windows_required: number;
    clean_windows_observed: number;
    recovery_threshold: number;
  };
};

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Aegis API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const getFleet = () => apiJson<FleetDeviceResponse[]>("/api/v1/fleet");
export const getDeviceState = (deviceId: string) =>
  apiJson<AegisDeviceState>(`/api/v1/devices/${encodeURIComponent(deviceId)}/state`);
