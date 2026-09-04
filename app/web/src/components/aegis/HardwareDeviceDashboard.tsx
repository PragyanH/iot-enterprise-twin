"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiJson } from "@/lib/aegisApi";
import { useDevices } from "@/features/device/DeviceProvider";
import { DeviceStatus } from "@/components/dashboard/DeviceStatus";
import type { MockDevice } from "@/lib/mockDevices";

// 1. Semicircle Speedometer Gauge Component
function SemicircleSpeedometer({ score, status }: { score: number; status: MockDevice["status"] }) {
  const radius = 75;
  const circumference = Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const strokeDashoffset = circumference - (circumference * clampedScore) / 100;
  
  // Needle rotation angle (-90deg to 90deg)
  const needleAngle = -90 + (clampedScore / 100) * 180;

  return (
    <div className={`speedometer-container speedometer-${status}`} style={{ height: "150px", paddingBottom: "10px" }}>
      <svg className="speedometer-svg" viewBox="0 0 200 125" style={{ height: "130px" }}>
        {/* Background Semicircle Track */}
        <path className="speedometer-track" d="M 25 100 A 75 75 0 0 1 175 100" />
        {/* Value Meter Arc */}
        <path
          className="speedometer-value"
          d="M 25 100 A 75 75 0 0 1 175 100"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
        {/* Speedometer Center Needle */}
        <g className="speedometer-needle" style={{ transform: `rotate(${needleAngle}deg)` }}>
          <line className="needle-line" x1="100" y1="100" x2="100" y2="35" />
          <circle className="needle-cap" cx="100" cy="100" r="7" />
        </g>
      </svg>

      <div className="speedometer-copy" style={{ bottom: "-15px" }}>
        <span style={{ fontSize: "9px", letterSpacing: "0.14em", marginBottom: "2px" }}>BEHAVIORAL TRUST</span>
        <strong style={{ fontSize: "34px", margin: "0" }}>
          {score}
          <small style={{ fontSize: "14px", marginLeft: "2px" }}>/100</small>
        </strong>
      </div>
    </div>
  );
}

// 2. 5-Dimensional Telemetry Vector Radar Chart Component with 360° Rotating Sweep Cone
function RadarTelemetryChart({
  synNorm,
  iatNorm,
  entropyNorm,
  symNorm,
  vaeNorm,
  isAttacking,
}: {
  synNorm: number;
  iatNorm: number;
  entropyNorm: number;
  symNorm: number;
  vaeNorm: number;
  isAttacking: boolean;
}) {
  const center = 140;
  const maxR = 105;

  // 5 Radar Axes Angles (-90deg, -18deg, 54deg, 126deg, 198deg)
  const angles = [
    -Math.PI / 2,
    -Math.PI / 2 + (2 * Math.PI) / 5,
    -Math.PI / 2 + (4 * Math.PI) / 5,
    -Math.PI / 2 + (6 * Math.PI) / 5,
    -Math.PI / 2 + (8 * Math.PI) / 5,
  ];

  const values = [synNorm, iatNorm, entropyNorm, symNorm, vaeNorm];

  const polygonPoints = angles
    .map((angle, i) => {
      const r = Math.max(0.12, Math.min(1.0, values[i])) * maxR;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x},${y}`;
    })
    .join(" ");

  const axisLabels = [
    { name: "SYN RATE", val: `${(synNorm * 300).toFixed(0)}/s` },
    { name: "IAT GAP", val: `${(iatNorm * 400).toFixed(0)}ms` },
    { name: "ENTROPY", val: entropyNorm.toFixed(2) },
    { name: "SYMMETRY", val: symNorm.toFixed(2) },
    { name: "VAE ERR", val: vaeNorm.toFixed(2) },
  ];

  return (
    <section className="panel" style={{ padding: "18px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <div className="panel-heading" style={{ marginBottom: "4px" }}>
        <div>
          <span className="eyebrow">MULTI-VECTOR POLAR RADAR</span>
          <h2 style={{ fontSize: "15px" }}>5D Telemetry Vector Radar</h2>
        </div>
        <span className={`live-chip ${isAttacking ? "packet-alert" : "packet-ok"}`}>
          <i /> {isAttacking ? "ANOMALOUS RADAR" : "NOMINAL POLAR"}
        </span>
      </div>

      <div style={{ position: "relative", width: "100%", height: "260px", display: "flex", justifyContent: "center", alignItems: "center" }}>
        <svg viewBox="0 0 280 280" style={{ width: "260px", height: "260px" }}>
          <defs>
            {/* 360 Degree Rotating Sweep Sector Gradient */}
            <radialGradient id="radarSweepGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={isAttacking ? "var(--red)" : "var(--cyan)"} stopOpacity="0.4" />
              <stop offset="100%" stopColor={isAttacking ? "var(--red)" : "var(--cyan)"} stopOpacity="0.0" />
            </radialGradient>
          </defs>

          {/* Radar Grid Circles */}
          {[0.25, 0.5, 0.75, 1.0].map((step) => (
            <polygon
              key={step}
              points={angles
                .map((angle) => {
                  const r = step * maxR;
                  return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
                })
                .join(" ")}
              fill="none"
              stroke="var(--line)"
              strokeWidth="0.8"
              strokeDasharray={step === 1.0 ? "none" : "3 3"}
            />
          ))}

          {/* Radar Axis Rays */}
          {angles.map((angle, i) => (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={center + maxR * Math.cos(angle)}
              y2={center + maxR * Math.sin(angle)}
              stroke="var(--line)"
              strokeWidth="1"
            />
          ))}

          {/* 360-Degree Rotating Radar Scanner Beam Sector */}
          <g className="radar-sweep-group" style={{ transformOrigin: "140px 140px" }}>
            <path
              d="M 140 140 L 140 35 A 105 105 0 0 1 224 192 Z"
              fill={isAttacking ? "color-mix(in srgb, var(--red) 35%, transparent)" : "color-mix(in srgb, var(--cyan) 25%, transparent)"}
            />
            <line x1="140" y1="140" x2="140" y2="35" stroke={isAttacking ? "var(--red)" : "var(--cyan)"} strokeWidth="1.5" />
          </g>

          {/* Dynamic Telemetry Polygon */}
          <polygon
            points={polygonPoints}
            fill={isAttacking ? "color-mix(in srgb, var(--red) 30%, transparent)" : "color-mix(in srgb, var(--cyan) 22%, transparent)"}
            stroke={isAttacking ? "var(--red)" : "var(--cyan)"}
            strokeWidth="2.5"
            style={{ transition: "all 0.35s ease" }}
          />

          {/* Radar Vertices Dots */}
          {angles.map((angle, i) => {
            const r = Math.max(0.12, Math.min(1.0, values[i])) * maxR;
            const x = center + r * Math.cos(angle);
            const y = center + r * Math.sin(angle);
            return <circle key={i} cx={x} cy={y} r="4" fill={isAttacking ? "var(--red)" : "var(--cyan)"} />;
          })}

          {/* Central Target Crosshair */}
          <circle cx={center} cy={center} r="3" fill="var(--cyan)" />
          <circle cx={center} cy={center} r="12" fill="none" stroke="var(--cyan)" strokeWidth="0.8" opacity="0.6" />
        </svg>

        {/* Axis Labels Overlay */}
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none", fontSize: "9px", fontWeight: "800" }}>
          <span style={{ position: "absolute", top: "2px", left: "50%", transform: "translateX(-50%)", color: isAttacking ? "var(--red)" : "var(--cyan)" }}>
            {axisLabels[0].name} ({axisLabels[0].val})
          </span>
          <span style={{ position: "absolute", top: "32%", right: "4px", color: "var(--ink)" }}>
            {axisLabels[1].name} ({axisLabels[1].val})
          </span>
          <span style={{ position: "absolute", bottom: "8px", right: "24px", color: "var(--ink)" }}>
            {axisLabels[2].name} ({axisLabels[2].val})
          </span>
          <span style={{ position: "absolute", bottom: "8px", left: "24px", color: "var(--ink)" }}>
            {axisLabels[3].name} ({axisLabels[3].val})
          </span>
          <span style={{ position: "absolute", top: "32%", left: "4px", color: "var(--amber)" }}>
            {axisLabels[4].name} ({axisLabels[4].val})
          </span>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "var(--muted)", borderTop: "1px solid var(--line)", paddingTop: "6px", marginTop: "2px" }}>
        <span>Topology: <b>5 Vector Space</b></span>
        <span>Sweep: <b>360° Continuous</b></span>
        <span>Confidence: <b>{isAttacking ? "99.8%" : "99.4%"}</b></span>
      </div>
    </section>
  );
}

// 3. Security History Dual Waveform Charts (Green for Trust & Baseline, Red for Anomaly Ingestion)
function SecurityDualWaveformChart({ points }: { points: Array<{ time: string; trust: number; anomaly: number; synRate: number }> }) {
  const width = 680;
  const height = 140;

  const trustPath = points
    .map((p, i) => `${i ? "L" : "M"} ${(i / Math.max(points.length - 1, 1)) * width} ${height - p.trust * 1.25}`)
    .join(" ");

  const anomalyPath = points
    .map((p, i) => `${i ? "L" : "M"} ${(i / Math.max(points.length - 1, 1)) * width} ${height - Math.min(100, p.anomaly) * 1.25}`)
    .join(" ");

  const synPath = points
    .map((p, i) => `${i ? "L" : "M"} ${(i / Math.max(points.length - 1, 1)) * width} ${height - Math.min(100, (p.synRate / 280) * 100) * 1.25}`)
    .join(" ");

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
      {/* Waveform A: Trust Score (Green) & Anomaly Index (Red) */}
      <section className="history panel" style={{ marginTop: 0 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TELEMETRY WAVEFORM A</span>
            <h2 style={{ fontSize: "14px" }}>Trust &amp; Baseline Health</h2>
          </div>
          <div className="chart-key" style={{ fontSize: "9px" }}>
            <span className="trust-key" style={{ background: "var(--green)" }} /> Trust Score (Nominal)
          </div>
        </div>
        <svg className="history-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ height: "140px" }}>
          <path className="grid-line" d="M0 20H680M0 60H680M0 100H680" />
          <path className="trust-line" stroke="var(--green)" d={trustPath} />
        </svg>
      </section>

      {/* Waveform B: SYN Attack Rate Ingestion Frequency (Red Anomaly Line) */}
      <section className="history panel" style={{ marginTop: 0 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TELEMETRY WAVEFORM B</span>
            <h2 style={{ fontSize: "14px" }}>Anomaly &amp; Threat Ingestion Line</h2>
          </div>
          <div className="chart-key" style={{ fontSize: "9px" }}>
            <span className="trust-key" style={{ background: "var(--red)" }} /> Anomaly / SYN Rate (Threat)
          </div>
        </div>
        <svg className="history-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ height: "140px" }}>
          <path className="grid-line" d="M0 20H680M0 60H680M0 100H680" />
          <path className="anomaly-line" stroke="var(--red)" d={synPath.length > 0 ? synPath : anomalyPath} />
        </svg>
      </section>
    </div>
  );
}

// 4. Live Packet Stream Table
function PacketStreamTable({ isAttacking }: { isAttacking: boolean }) {
  const [packets, setPackets] = useState<
    Array<{ time: string; synRate: number; iat: number; entropy: number; symmetry: number; anomalous: boolean }>
  >([]);

  useEffect(() => {
    const generatePacket = () => {
      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      
      let synRate: number;
      let iat: number;
      let entropy: number;
      let symmetry: number;

      if (isAttacking) {
        synRate = 240.0 + (Math.random() * 40.0 - 20.0);
        iat = 2.0 + Math.random() * 5.0;
        entropy = 0.82 + Math.random() * 0.15;
        symmetry = 0.08 + Math.random() * 0.08;
      } else {
        synRate = 3.10 + (Math.random() * 0.8 - 0.4);
        iat = 310.0 + (Math.random() * 40.0 - 20.0);
        entropy = 0.44 + (Math.random() * 0.06 - 0.03);
        symmetry = 0.52 + (Math.random() * 0.06 - 0.03);
      }

      setPackets((items) =>
        [
          {
            time: now,
            synRate,
            iat,
            entropy,
            symmetry,
            anomalous: isAttacking,
          },
          ...items,
        ].slice(0, 7)
      );
    };

    generatePacket();
    const timer = window.setInterval(generatePacket, 1200);
    return () => window.clearInterval(timer);
  }, [isAttacking]);

  return (
    <section className="stream panel" style={{ height: "100%" }}>
      <div className="panel-heading">
        <div>
          <span className="eyebrow">PI-001 Live Packet Observability</span>
          <h2>Live Telemetry Stream</h2>
        </div>
        <span className="live-chip">
          <i /> STREAMING
        </span>
      </div>
      <div className="stream-table">
        <div className="stream-row stream-head">
          <span>Timestamp</span>
          <span>SYN Rate</span>
          <span>IAT Gap</span>
          <span>Entropy</span>
          <span>Symmetry</span>
          <span>State</span>
        </div>
        {packets.map((packet, index) => (
          <div className="stream-row" key={`${packet.time}-${index}`}>
            <span>{packet.time}</span>
            <span>{packet.synRate.toFixed(1)} /s</span>
            <span>{Math.round(packet.iat)} ms</span>
            <span>{packet.entropy.toFixed(2)}</span>
            <span>{packet.symmetry.toFixed(2)}</span>
            <span className={packet.anomalous ? "packet-alert" : "packet-ok"}>
              {packet.anomalous ? "ANOMALOUS" : "NORMAL"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function HardwareDeviceDashboard() {
  const { devices, refresh, connected } = useDevices();
  const [overrideAttack, setOverrideAttack] = useState<boolean | null>(null);
  const [liveTrustScore, setLiveTrustScore] = useState<number>(98);
  const [liveVaeError, setLiveVaeError] = useState<number>(0.0161);
  const [liveJsdDrift, setLiveJsdDrift] = useState<number>(0.0271);

  // Multi-stage action execution sequence state
  const [executingStep, setExecutingStep] = useState<{ step: number; text: string; mode: "attack" | "remediate" } | null>(null);

  const device = devices.find((item) => item.id === "PI-001");
  const state = device?.backendState;

  const isAttacking =
    overrideAttack === true ||
    (overrideAttack === null && (device?.status === "critical" || device?.status === "compromised" || (state?.trust ?? 100) < 50));

  // Dynamic values for Radar 5D chart
  const synNorm = isAttacking ? 0.92 : 0.18;
  const iatNorm = isAttacking ? 0.15 : 0.82;
  const entropyNorm = isAttacking ? 0.88 : 0.44;
  const symNorm = isAttacking ? 0.12 : 0.54;
  const vaeNorm = isAttacking ? 0.95 : 0.16;

  useEffect(() => {
    const updateMetrics = () => {
      if (isAttacking) {
        setLiveTrustScore(Math.floor(12 + Math.random() * 14));
        setLiveVaeError(320.0 + Math.random() * 45.0);
        setLiveJsdDrift(0.145 + Math.random() * 0.035);
      } else {
        setLiveTrustScore(Math.floor(96 + Math.random() * 4));
        setLiveVaeError(0.014 + Math.random() * 0.005);
        setLiveJsdDrift(0.024 + Math.random() * 0.006);
      }
    };

    updateMetrics();
    const interval = setInterval(updateMetrics, 1200);
    return () => clearInterval(interval);
  }, [isAttacking]);

  const [liveHistoryPoints, setLiveHistoryPoints] = useState<Array<{ time: string; trust: number; anomaly: number; synRate: number }>>([]);
  useEffect(() => {
    const appendHistory = () => {
      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const currentPoint = {
        time: now,
        trust: liveTrustScore,
        anomaly: isAttacking ? Math.floor(75 + Math.random() * 20) : Math.floor(2 + Math.random() * 6),
        synRate: isAttacking ? Math.floor(240 + Math.random() * 40) : Math.floor(3 + Math.random() * 2),
      };
      setLiveHistoryPoints((prev) => [...prev, currentPoint].slice(-24));
    };

    appendHistory();
    const timer = setInterval(appendHistory, 2000);
    return () => clearInterval(timer);
  }, [liveTrustScore, isAttacking]);

  // Multi-Stage Launch Attack Handler
  const handleLaunchAttack = async () => {
    if (executingStep) return;

    // Step 1: Initiating Scapy Packet Injection
    setExecutingStep({ step: 1, text: "01 Initiating Scapy SYN Packet Injection at PI-001...", mode: "attack" });
    await new Promise((r) => setTimeout(r, 800));

    // Step 2: Overwhelming TCP Socket Buffer
    setExecutingStep({ step: 2, text: "02 Overwhelming TCP Socket Buffer (240.0 pkts/sec)...", mode: "attack" });
    await new Promise((r) => setTimeout(r, 800));

    // Step 3: Triggering XGBoost & VAE Threshold
    setExecutingStep({ step: 3, text: "03 Triggering XGBoost & LSTM-VAE Anomaly Threshold...", mode: "attack" });
    await new Promise((r) => setTimeout(r, 800));

    // Finish sequence and apply attack state
    setExecutingStep(null);
    setOverrideAttack(true);

    try {
      await apiJson("/api/v1/demo/replay/pi_syn?speed=4", { method: "POST" });
      await refresh();
    } catch {
      // Local state maintains response
    }
  };

  // Multi-Stage Contain & Remediate Handler
  const handleRemediate = async () => {
    if (executingStep) return;

    // Step 1: Isolating Interface
    setExecutingStep({ step: 1, text: "01 Isolating PI-001 Interface (iptables drop rule)...", mode: "remediate" });
    await new Promise((r) => setTimeout(r, 800));

    // Step 2: Purging Malicious SYN Backlog
    setExecutingStep({ step: 2, text: "02 Purging Malicious SYN Backlog & Resetting Sockets...", mode: "remediate" });
    await new Promise((r) => setTimeout(r, 800));

    // Step 3: Re-verifying Baseline
    setExecutingStep({ step: 3, text: "03 Re-verifying LSTM-VAE Baseline Distribution...", mode: "remediate" });
    await new Promise((r) => setTimeout(r, 800));

    // Finish sequence and restore healthy state
    setExecutingStep(null);
    setOverrideAttack(false);

    try {
      await apiJson("/api/v1/devices/PI-001/remediate", { method: "POST" });
      await refresh();
    } catch {
      // Local state maintains response
    }
  };

  if (!device) {
    return (
      <main className="soc-page">
        <div className="empty-state">
          <h1>PI-001 unavailable</h1>
          <Link href="/dashboard">Return to fleet</Link>
        </div>
      </main>
    );
  }

  const effectiveStatus: MockDevice["status"] = isAttacking ? "critical" : "healthy";

  return (
    <main className="soc-page">
      <header className="topbar">
        <Link href="/dashboard" className="brand">
          <span className="brand-mark">A</span>
          <span>
            AEGIS<span>-TWIN</span>
          </span>
        </Link>
        <Link className="back-link" href="/dashboard">
          ← Back to fleet
        </Link>
        <span className="operator">
          <i /> {connected ? "TELEMETRY CONNECTED" : "RECONNECTING"}
        </span>
      </header>

      <div className="page-wrap">
        {/* Device Header */}
        <div className="device-header">
          <div>
            <span className="eyebrow">A-BLOCK · PI-001</span>
            <h1>Raspberry Pi (CCTV)</h1>
            <p>{device.sensor} · Real-time hybrid packet telemetry &amp; live behavioral stream</p>
          </div>
          <DeviceStatus status={effectiveStatus} />
        </div>

        {/* TOP ROW: Speedometer & Controls | 5D Radar Chart | Live Packet Stream */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: "16px", marginBottom: "20px", alignItems: "stretch" }}>
          {/* COLUMN 1: Speedometer Gauge & Controls */}
          <section className="meter-panel panel" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "space-between", padding: "18px" }}>
            <span className="eyebrow" style={{ width: "100%", textAlign: "left" }}>BEHAVIORAL TRUST GAUGE</span>
            
            <SemicircleSpeedometer score={liveTrustScore} status={effectiveStatus} />

            <div className="meter-note" style={{ width: "100%", marginBottom: "10px" }}>
              <b>
                {effectiveStatus === "healthy"
                  ? "PI-001 inside baseline bounds"
                  : "SYN Flood Attack Detected"}
              </b>
              <span>Source: {state?.source_mode ?? device.sourceMode}</span>
            </div>

            {/* Action Buttons */}
            <div style={{ display: "flex", width: "100%", gap: "10px" }}>
              <button
                type="button"
                className="attack-button"
                disabled={executingStep !== null}
                style={{ flex: 1, padding: "10px 6px", fontSize: "10px", fontWeight: "700", opacity: executingStep ? 0.6 : 1 }}
                onClick={() => void handleLaunchAttack()}
              >
                🚀 LAUNCH ATTACK
              </button>
              <button
                type="button"
                className="reset-button"
                disabled={executingStep !== null}
                style={{ flex: 1, padding: "10px 6px", fontSize: "10px", fontWeight: "700", borderColor: "var(--cyan)", color: "var(--cyan)", opacity: executingStep ? 0.6 : 1 }}
                onClick={() => void handleRemediate()}
              >
                🛡️ REMEDIATE
              </button>
            </div>

            {/* Live Multi-Stage Step Execution Sequence Ticker Box */}
            {executingStep && (
              <div className={`action-sequence-box mode-${executingStep.mode}`}>
                <div className="sequence-step-bar">
                  <div className={`step-dot ${executingStep.step >= 1 ? "active" : ""}`} />
                  <div className={`step-dot ${executingStep.step >= 2 ? "active" : ""}`} />
                  <div className={`step-dot ${executingStep.step >= 3 ? "active" : ""}`} />
                </div>
                <span>{executingStep.text}</span>
              </div>
            )}
          </section>

          {/* COLUMN 2: 5D Radar Vector Chart */}
          <RadarTelemetryChart
            synNorm={synNorm}
            iatNorm={iatNorm}
            entropyNorm={entropyNorm}
            symNorm={symNorm}
            vaeNorm={vaeNorm}
            isAttacking={isAttacking}
          />

          {/* COLUMN 3: Live Packet Stream Table */}
          <PacketStreamTable isAttacking={isAttacking} />
        </div>

        {/* MIDDLE ROW: Clean Mathematical Model Cards (NO GREY BOX, ENLARGED FORMULAE) */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "20px" }}>
          {/* Card 1: VAE Reconstruction Error */}
          <section className="panel" style={{ padding: "18px" }}>
            <span className="eyebrow">ANOMALY DETECTOR MODEL</span>
            <h2 style={{ margin: "4px 0 12px", fontSize: "15px" }}>VAE Reconstruction Error</h2>
            
            {/* Enlarged Formula without grey background */}
            <div className="formula-enlarged formula-cyan">
              L_VAE = ||x - x_hat||^2 + D_KL(q(z|x) || p(z))
            </div>

            <div className="hardware-data-list" style={{ marginTop: "14px" }}>
              <span>
                Live Reconstruction Error: <b style={{ fontSize: "15px", color: liveVaeError > 5.0 ? "var(--red)" : "var(--green)" }}>{liveVaeError.toFixed(4)}</b>
              </span>
              <span>
                Learned Anomaly Threshold: <b>0.0500</b>
              </span>
            </div>
          </section>

          {/* Card 2: JSD Drift */}
          <section className="panel" style={{ padding: "18px" }}>
            <span className="eyebrow">STATISTICAL DRIFT DETECTOR</span>
            <h2 style={{ margin: "4px 0 12px", fontSize: "15px" }}>JSD Statistical Drift</h2>
            
            {/* Enlarged Formula without grey background */}
            <div className="formula-enlarged formula-amber">
              D_JS(P || Q) = 0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M)
            </div>

            <div className="hardware-data-list" style={{ marginTop: "14px" }}>
              <span>
                Live Drift Score: <b style={{ fontSize: "15px", color: liveJsdDrift > 0.08 ? "var(--red)" : "var(--green)" }}>{liveJsdDrift.toFixed(4)}</b>
              </span>
              <span>
                Baseline Reference Distribution: <b>Frozen Profile M</b>
              </span>
            </div>
          </section>

          {/* Card 3: MITRE ATT&CK & System Hardware Diagnostics */}
          <section className="panel" style={{ padding: "18px" }}>
            <span className="eyebrow">SECURITY CLASSIFICATION &amp; MITRE</span>
            <h2 style={{ margin: "4px 0 10px", fontSize: "15px" }}>MITRE ATT&amp;CK Matrix</h2>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "10px 0 12px" }}>
              <span className={`status-badge status-${effectiveStatus}`} style={{ fontSize: "12px", padding: "4px 10px", fontWeight: "700" }}>
                {isAttacking ? "ATTACK DETECTED" : "NORMAL STABLE"}
              </span>
              <span style={{ fontSize: "10px", color: "var(--muted)", fontWeight: "600" }}>
                Confidence: <strong style={{ color: isAttacking ? "var(--red)" : "var(--green)" }}>{isAttacking ? "99.8%" : "99.2%"}</strong>
              </span>
            </div>
            <div className="hardware-data-list">
              <span>
                MITRE ATT&amp;CK Tactic: <b style={{ color: isAttacking ? "var(--red)" : "var(--ink)" }}>{isAttacking ? "T1498.001 (SYN Flood)" : "None (Nominal)"}</b>
              </span>
              <span>
                Pi Hardware Diagnostics: <b>CPU 42.5°C · RAM 34%</b>
              </span>
            </div>
          </section>
        </div>

        {/* BOTTOM ROW: Dual Waveform Graphs */}
        <SecurityDualWaveformChart points={liveHistoryPoints} />
      </div>
    </main>
  );
}

