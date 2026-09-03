import type { DeviceStatus, MockDevice, TrafficMetrics } from "./mockDevices";

export const metricKeys = ["packetSize", "interArrivalTime", "entropy", "symmetry"] as const;
export type MetricKey = (typeof metricKeys)[number];
export const calculateDeviation = (current: number, baseline: number) => Math.abs(current - baseline) / Math.max(baseline, .001);
export const calculateAnomalyScore = (device: Pick<MockDevice, "baseline" | "current">) => metricKeys.reduce((sum, key) => sum + calculateDeviation(device.current[key], device.baseline[key]) * 25, 0);
export const calculateTrustScore = (device: Pick<MockDevice, "baseline" | "current">) => Math.max(0, Math.min(100, Math.round(100 - calculateAnomalyScore(device))));
export function calculateDeviceStatus(trustScore: number, device?: Pick<MockDevice, "baseline" | "current" | "thresholds">): DeviceStatus {
  if (device) {
    const maximumDeviation = Math.max(...metricKeys.map((key) => calculateDeviation(device.current[key], device.baseline[key])));
    if (maximumDeviation > .5 || trustScore < 40) return "critical";
    if (maximumDeviation > .25 || trustScore < 70) return "compromised";
    if (maximumDeviation > .1 || metricKeys.some((key) => calculateDeviation(device.current[key], device.baseline[key]) > device.thresholds[key])) return "warning";
  }
  return trustScore >= 90 ? "healthy" : trustScore >= 70 ? "warning" : trustScore >= 40 ? "compromised" : "critical";
}
export const statusLabel = (status: DeviceStatus) => status === "healthy" ? "HEALTHY" : status.toUpperCase();
export const metricUnit = (key: MetricKey) => key === "packetSize" ? "bytes" : key === "interArrivalTime" ? "ms" : "ratio";
export const scaleMetric = (key: MetricKey, value: number) => key === "entropy" || key === "symmetry" ? value.toFixed(2) : Math.round(value).toString();
export const attackedMetrics = (baseline: TrafficMetrics): TrafficMetrics => ({ packetSize: baseline.packetSize * 2.4, interArrivalTime: baseline.interArrivalTime * .18, entropy: Math.min(1, baseline.entropy + .42), symmetry: Math.max(.05, baseline.symmetry - .58) });