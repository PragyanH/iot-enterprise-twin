"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";
import { calculateAnomalyScore, metricKeys, metricUnit, scaleMetric, type MetricKey } from "@/lib/securityModel";
import { useDevices } from "@/features/device/DeviceProvider";
import { DeviceStatus } from "@/components/dashboard/DeviceStatus";

function TrustMeter({ score, status }: { score: number; status: MockDevice["status"] }) {
  const circumference = 2 * Math.PI * 82;
  return <div className={`trust-meter meter-${status}`}><svg viewBox="0 0 210 210"><circle className="meter-track" cx="105" cy="105" r="82" /><circle className="meter-value" cx="105" cy="105" r="82" strokeDasharray={circumference} strokeDashoffset={circumference - circumference * score / 100} /></svg><div className="meter-copy"><span>TRUST SCORE</span><strong>{score}<small>/100</small></strong><DeviceStatus status={status} /></div></div>;
}

function ParameterControls({ device, onChange, onAttack, onReset }: { device: MockDevice; onChange: (key: MetricKey, value: number) => void; onAttack: () => void; onReset: () => void }) {
  const labels: Record<MetricKey, string> = { packetSize: "Packet size", interArrivalTime: "Inter-arrival time", entropy: "Entropy", symmetry: "Symmetry" };
  return <section className="controls panel"><div className="panel-heading"><div><span className="eyebrow">Traffic signature</span><h2>Parameter controls</h2></div></div>{metricKeys.map((key) => { const baseline = device.baseline[key]; const value = device.current[key]; const min = key === "entropy" || key === "symmetry" ? 0 : baseline * .1; const max = key === "entropy" || key === "symmetry" ? 1 : baseline * 3; return <label className="range-control" key={key}><span><b>{labels[key]}</b><em>{scaleMetric(key, value)} <small>{metricUnit(key)}</small></em></span><input type="range" min={min} max={max} step={key === "entropy" || key === "symmetry" ? .01 : 1} value={value} onChange={(event) => onChange(key, Number(event.target.value))} /><small className="baseline">BASELINE {scaleMetric(key, baseline)} {metricUnit(key)}</small></label>; })}<div className="control-actions"><button className="attack-button" onClick={onAttack}>⚠ LAUNCH ATTACK</button><button className="reset-button" onClick={onReset}>REMEDIATE &amp; RESTORE</button></div></section>;
}

function PacketStream({ device }: { device: MockDevice }) {
  const [packets, setPackets] = useState<Array<{ time: string; metrics: MockDevice["current"]; anomalous: boolean }>>([]);

  useEffect(() => {
    const add = () => {
      const isAttacking = device.status !== "healthy";
      // Generate realistic dynamic variations for mock stream
      const sizeNoise = (Math.random() - 0.5) * (isAttacking ? 120 : 18);
      const gapNoise = (Math.random() - 0.5) * (isAttacking ? 60 : 14);
      const entropyNoise = (Math.random() - 0.5) * 0.04;
      const symmetryNoise = (Math.random() - 0.5) * 0.04;

      const dynamicMetrics: MockDevice["current"] = {
        packetSize: Math.max(64, device.current.packetSize + sizeNoise),
        interArrivalTime: Math.max(10, device.current.interArrivalTime + gapNoise),
        entropy: Math.min(1.0, Math.max(0.0, device.current.entropy + entropyNoise)),
        symmetry: Math.min(1.0, Math.max(0.0, device.current.symmetry + symmetryNoise)),
      };

      setPackets((items) => [
        {
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          metrics: dynamicMetrics,
          anomalous: isAttacking,
        },
        ...items,
      ].slice(0, 8));
    };

    add();
    const timer = window.setInterval(add, 1600);
    return () => window.clearInterval(timer);
  }, [device]);

  return (
    <section className="stream panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Network observability</span>
          <h2>Live telemetry stream</h2>
        </div>
        <span className="live-chip"><i /> STREAMING</span>
      </div>
      <div className="stream-table">
        <div className="stream-row stream-head">
          <span>Timestamp</span>
          <span>Size</span>
          <span>Gap</span>
          <span>Entropy</span>
          <span>Symmetry</span>
          <span>State</span>
        </div>
        {packets.map((packet, index) => (
          <div className="stream-row" key={`${packet.time}-${index}`}>
            <span>{packet.time}</span>
            <span>{Math.round(packet.metrics.packetSize)} B</span>
            <span>{Math.round(packet.metrics.interArrivalTime)} ms</span>
            <span>{packet.metrics.entropy.toFixed(2)}</span>
            <span>{packet.metrics.symmetry.toFixed(2)}</span>
            <span className={packet.anomalous ? "packet-alert" : "packet-ok"}>
              {packet.anomalous ? "ANOMALOUS" : "NORMAL"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function SecurityHistory({ points }: { points: Array<{ time: string; trust: number; anomaly: number }> }) {
  const width = 720; const height = 190;
  const path = (key: "trust" | "anomaly") => points.map((point, index) => `${index ? "L" : "M"} ${(index / Math.max(points.length - 1, 1)) * width} ${height - point[key] * 1.65}`).join(" ");
  return <section className="history panel"><div className="panel-heading"><div><span className="eyebrow">Behavior over time</span><h2>Security / attack history</h2></div><div className="chart-key"><span className="trust-key" />Trust score <span className="anomaly-key" />Anomaly level</div></div><svg className="history-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"><path className="grid-line" d="M0 25H720M0 82H720M0 140H720M0 188H720" /><path className="trust-line" d={path("trust")} /><path className="anomaly-line" d={path("anomaly")} /></svg><div className="chart-scale"><span>100</span><span>50</span><span>0</span></div></section>;
}

export function DeviceDashboard({ deviceId }: { deviceId: string }) {
  const { devices, histories, updateMetric, attack, reset } = useDevices();
  const device = devices.find((item) => item.id === deviceId);
  if (!device) return <main className="soc-page"><div className="empty-state"><h1>Device not found</h1><Link href="/dashboard">Return to fleet</Link></div></main>;
  return <main className="soc-page"><header className="topbar"><Link href="/dashboard" className="brand"><span className="brand-mark">A</span><span>AEGIS<span>-TWIN</span></span></Link><Link className="back-link" href="/dashboard">← Back to fleet</Link><span className="operator"><i /> {device.sourceMode?.replaceAll("_", " ")}</span></header><div className="page-wrap"><div className="device-header"><div><span className="eyebrow">Device telemetry / {device.location}</span><h1>{device.id} <span>/ {device.name}</span></h1><p>{device.type} · {device.sensor} · backend baseline locked</p></div><DeviceStatus status={device.status} /></div><div className="device-detail-layout"><div className="device-detail-main"><div className="device-top-grid"><section className="meter-panel panel"><TrustMeter score={device.trustScore} status={device.status} /><div className="meter-note"><b>{device.status === "healthy" ? "Within expected behavior" : `${device.attackType?.replaceAll("_", " ")} detected`}</b><span>Hybrid risk {Math.round((device.backendState?.risk ?? calculateAnomalyScore(device) / 100) * 100)}%</span></div></section><PacketStream device={device} /></div><SecurityHistory points={histories[device.id] ?? []} /></div><div className="controls-rail"><ParameterControls device={device} onChange={(key, value) => updateMetric(device.id, key, value)} onAttack={() => attack(device.id)} onReset={() => reset(device.id)} /></div></div></div></main>;
}
