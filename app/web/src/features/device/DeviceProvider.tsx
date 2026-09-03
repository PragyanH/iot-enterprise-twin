"use client";

import { createContext, useContext, useMemo, useState } from "react";
import { attackedMetrics, calculateAnomalyScore, calculateDeviceStatus, calculateTrustScore, type MetricKey } from "@/lib/securityModel";
import { mockDevices, type MockDevice, type TrafficMetrics } from "@/lib/mockDevices";

type HistoryPoint = { time: string; trust: number; anomaly: number };
type DeviceContextValue = { devices: MockDevice[]; histories: Record<string, HistoryPoint[]>; updateMetric: (id: string, key: MetricKey, value: number) => void; attack: (id: string) => void; reset: (id: string) => void };
const DeviceContext = createContext<DeviceContextValue | null>(null);

const historyFor = (device: MockDevice): HistoryPoint[] => Array.from({ length: 12 }, (_, index) => ({ time: `${String(9 + Math.floor(index / 2)).padStart(2, "0")}:${index % 2 ? "30" : "00"}`, trust: Math.max(72, 96 - index * 1.4), anomaly: Math.min(28, 4 + index * 1.8) }));
const stamp = (trust: number, anomaly: number): HistoryPoint => ({ time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), trust, anomaly });

export function DeviceProvider({ children }: { children: React.ReactNode }) {
  const [devices, setDevices] = useState(mockDevices);
  const [histories, setHistories] = useState<Record<string, HistoryPoint[]>>(() => Object.fromEntries(mockDevices.map((device) => [device.id, historyFor(device)])));

  const commit = (id: string, current: TrafficMetrics) => {
    setDevices((items) => items.map((device) => {
      if (device.id !== id) return device;
      const next = { ...device, current, trustScore: calculateTrustScore({ baseline: device.baseline, current }), status: "healthy" as MockDevice["status"] };
      next.status = calculateDeviceStatus(next.trustScore, next);
      setHistories((previous) => ({ ...previous, [id]: [...(previous[id] ?? []), stamp(next.trustScore, Math.round(calculateAnomalyScore(next)))].slice(-24) }));
      return next;
    }));
  };
  const value = useMemo<DeviceContextValue>(() => ({ devices, histories, updateMetric: (id, key, value) => { const found = devices.find((device) => device.id === id); if (found) commit(id, { ...found.current, [key]: value }); }, attack: (id) => { const found = devices.find((device) => device.id === id); if (found) commit(id, attackedMetrics(found.baseline)); }, reset: (id) => { const found = devices.find((device) => device.id === id); if (found) commit(id, { ...found.baseline }); } }), [devices, histories]);
  return <DeviceContext.Provider value={value}>{children}</DeviceContext.Provider>;
}

export function useDevices() { const value = useContext(DeviceContext); if (!value) throw new Error("useDevices must be used inside DeviceProvider"); return value; }