"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { apiJson, getDeviceState, getFleet, type AegisDeviceState, type FleetDeviceResponse } from "@/lib/aegisApi";
import { calculateAnomalyScore, type MetricKey } from "@/lib/securityModel";
import { mockDevices, type DeviceStatus, type DeviceType, type MockDevice, type TrafficMetrics } from "@/lib/mockDevices";

type HistoryPoint = { time: string; trust: number; anomaly: number };
type DeviceContextValue = { devices: MockDevice[]; histories: Record<string, HistoryPoint[]>; connected: boolean; error: string | null; refresh: () => Promise<void>; updateMetric: (id: string, key: MetricKey, value: number) => void; attack: (id: string) => void; reset: (id: string) => void };
const DeviceContext = createContext<DeviceContextValue | null>(null);
const thresholds: TrafficMetrics = { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .25 };
const typeFor = (item: FleetDeviceResponse): DeviceType => {
  const name = item.name.toLowerCase();
  if (item.source === "pi" || name.includes("camera")) return "Camera";
  if (name.includes("pump")) return "Pressure Sensor";
  if (name.includes("gas") || name.includes("weather")) return "Air Quality Sensor";
  if (name.includes("lock")) return "Smart Lock";
  if (name.includes("printer")) return "Door Sensor";
  if (name.includes("smoke")) return "Smoke Detector";
  if (name.includes("temperature")) return "Temperature Sensor";
  if (name.includes("fire")) return "Fire Alarm";
  return "Motion Sensor";
};
const statusFor = (state: string): DeviceStatus => state === "ATTACK" ? "critical" : state === "HEALTHY" ? "healthy" : state === "SUSPICIOUS" ? "compromised" : "warning";
const trafficFrom = (features: Record<string, number>): TrafficMetrics => {
  const packetSize = Number(features.packet_size ?? 0);
  return { packetSize: packetSize <= 2 ? packetSize * 1000 : packetSize, interArrivalTime: Number(features.iat ?? 0) * 1000, entropy: Number(features.payload_entropy ?? 0), symmetry: Number(features.flow_symmetry ?? 0) };
};
const pointFor = (device: MockDevice): HistoryPoint => ({ time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), trust: device.trustScore, anomaly: Math.round(calculateAnomalyScore(device)) });

function toDevice(fleet: FleetDeviceResponse, state: AegisDeviceState): MockDevice {
  const baseline = trafficFrom(state.baseline_features ?? {});
  return { id: fleet.id, name: fleet.name, type: typeFor(fleet), location: fleet.sector, floor: fleet.id === "PI-001" ? 2 : 1, room: fleet.sector, baseline, current: trafficFrom(state.current_features ?? state.baseline_features ?? {}), thresholds, trustScore: Math.round(state.trust), status: statusFor(state.state), source: fleet.source, sourceMode: state.source_mode, sensor: state.sensor, attackType: state.attack_type, confidence: state.confidence, activeIncidentId: state.active_incident_id, backendState: state };
}

export function DeviceProvider({ children }: { children: React.ReactNode }) {
  const [devices, setDevices] = useState<MockDevice[]>(mockDevices);
  const [histories, setHistories] = useState<Record<string, HistoryPoint[]>>(() => Object.fromEntries(mockDevices.map((device) => [device.id, [pointFor(device)]])));
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshing = useRef(false);

  const refresh = useCallback(async () => {
    if (refreshing.current) return;
    refreshing.current = true;
    try {
      const fleet = await getFleet();
      const states = await Promise.all(fleet.map((item) => getDeviceState(item.id)));
      const next = fleet.map((item, index) => toDevice(item, states[index]));
      setDevices(next);
      setHistories((previous) => {
        const updated = { ...previous };
        for (const device of next) {
          const point = pointFor(device);
          const existing = updated[device.id] ?? [];
          const last = existing[existing.length - 1];
          updated[device.id] = last?.trust === point.trust && last?.anomaly === point.anomaly ? existing : [...existing, point].slice(-24);
        }
        return updated;
      });
      setConnected(true); setError(null);
    } catch (cause) {
      setConnected(false); setError(cause instanceof Error ? cause.message : "Backend unavailable");
    } finally { refreshing.current = false; }
  }, []);

  useEffect(() => {
    void refresh();
    const events = new EventSource("/api/v1/events/trust");
    events.addEventListener("trust", () => void refresh());
    events.onerror = () => { setConnected(false); setError("Live telemetry stream disconnected"); };
    return () => events.close();
  }, [refresh]);

  const submitMetric = useCallback(async (id: string, key: MetricKey, value: number) => {
    const found = devices.find((device) => device.id === id);
    if (!found || found.source !== "mock") return;
    const current = { ...found.current, [key]: value };
    try {
      await apiJson("/api/v1/telemetry/windows", { method: "POST", body: JSON.stringify({ device_id: id, source: "mock", sensor: "aegis-ui-controls", points: [{ packet_size: current.packetSize / 1000, iat: current.interArrivalTime / 1000, payload_entropy: current.entropy, flow_symmetry: current.symmetry }] }) });
      await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Telemetry update failed"); }
  }, [devices, refresh]);

  const runAction = useCallback(async (id: string, action: "simulate-attack" | "remediate") => {
    try { await apiJson(`/api/v1/devices/${encodeURIComponent(id)}/${action}`, { method: "POST" }); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Device action failed"); }
  }, [refresh]);

  const value = useMemo<DeviceContextValue>(() => ({ devices, histories, connected, error, refresh, updateMetric: (id, key, value) => void submitMetric(id, key, value), attack: (id) => void runAction(id, "simulate-attack"), reset: (id) => void runAction(id, "remediate") }), [devices, histories, connected, error, refresh, submitMetric, runAction]);
  return <DeviceContext.Provider value={value}>{children}</DeviceContext.Provider>;
}

export function useDevices() { const value = useContext(DeviceContext); if (!value) throw new Error("useDevices must be used inside DeviceProvider"); return value; }
