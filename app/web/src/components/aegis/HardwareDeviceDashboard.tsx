"use client";

import Link from "next/link";
import { useState } from "react";
import { apiJson } from "@/lib/aegisApi";
import { useDevices } from "@/features/device/DeviceProvider";
import { DeviceStatus } from "@/components/dashboard/DeviceStatus";

export function HardwareDeviceDashboard() {
  const { devices, refresh, connected } = useDevices();
  const [action, setAction] = useState<string | null>(null);
  const device = devices.find((item) => item.id === "PI-001");
  const state = device?.backendState;
  const execute = async (path: string, label: string) => {
    setAction(label);
    try { await apiJson(path, { method: "POST" }); await refresh(); setAction(`${label} requested`); }
    catch (cause) { setAction(cause instanceof Error ? cause.message : "Action failed"); }
  };
  if (!device) return <main className="soc-page"><div className="empty-state"><h1>PI-001 unavailable</h1><Link href="/dashboard">Return to fleet</Link></div></main>;
  return <main className="soc-page">
    <header className="topbar"><Link href="/dashboard" className="brand"><span className="brand-mark">A</span><span>AEGIS<span>-TWIN</span></span></Link><Link className="back-link" href="/dashboard">← Back to fleet</Link><span className="operator"><i /> {connected ? "TELEMETRY CONNECTED" : "RECONNECTING"}</span></header>
    <div className="page-wrap">
      <div className="device-header"><div><span className="eyebrow">{device.sourceMode?.replaceAll("_", " ")} · PI-001</span><h1>{device.name}</h1><p>{device.sensor} · one-second hybrid trust telemetry</p></div><DeviceStatus status={device.status} /></div>
      <div className="hardware-dashboard-grid">
        <section className="hardware-empty panel"><div className="hardware-empty-icon">PI</div><h2>Trust {device.trustScore}/100 · {state?.state ?? "BOOTSTRAP"}</h2><p>{state?.attack_type && state.attack_type !== "none" ? `Detected ${state.attack_type.replaceAll("_", " ")} at ${(state.confidence * 100).toFixed(0)}% confidence.` : "PI-001 is being evaluated against its frozen behavioral baseline."}</p><div className="hardware-data-list"><span>Source provenance <b>{state?.source_mode ?? device.sourceMode}</b></span><span>Active incident <b>{state?.active_incident_id ?? "None"}</b></span><span>MITRE ATT&CK <b>{state?.classification?.mitre?.technique_id ?? "Unmapped"}</b></span><span>Recovery verification <b>{state ? `${state.recovery_progress.clean_windows_observed}/${state.recovery_progress.clean_windows_required}` : "0/3"}</b></span></div><div className="control-actions"><button className="attack-button" onClick={() => void execute("/api/v1/demo/replay/pi_syn?speed=4", "SYN replay")}>RUN SYN REPLAY</button><button className="reset-button" onClick={() => void execute("/api/v1/devices/PI-001/remediate", "Remediation")}>CONTAIN &amp; REMEDIATE</button></div>{action && <small>{action}</small>}</section>
        <section className="hardware-placeholder-card panel"><span className="eyebrow">Live detector evidence</span><h2>Hybrid signals</h2><div className="hardware-data-list"><span>SYN rate <b>{state?.current_features?.syn_rate?.toFixed(2) ?? "--"}/s</b></span><span>Handshake completion <b>{state?.current_features?.handshake_completion_ratio?.toFixed(3) ?? "--"}</b></span><span>VAE reconstruction <b>{state?.reconstruction_error?.toFixed(4) ?? "--"}</b></span><span>JSD drift <b>{state?.jsd?.toFixed(4) ?? "--"}</b></span></div><small>{state?.detection_mode?.replaceAll("_", " ") ?? "Waiting for telemetry"}</small></section>
        <section className="hardware-placeholder-card panel"><span className="eyebrow">Top contributors</span><h2>Behavioral deviations</h2><div className="hardware-data-list">{state?.top_anomalies?.slice(0, 5).map((item) => <span key={item.feature}>{item.feature.replaceAll("_", " ")} <b>{(item.score * 100).toFixed(1)}% · {item.direction}</b></span>) ?? <span>Evidence <b>Waiting</b></span>}</div><small>Model: LSTM-VAE + XGBoost + JSD + rules</small></section>
      </div>
    </div>
  </main>;
}
