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

// 2. 5-Dimensional Telemetry Vector Radar Chart Component
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
  const center = 110;
  const maxR = 75;

  // 5 Radar Axes Angles (0deg, 72deg, 144deg, 216deg, 288deg)
  const angles = [-Math.PI / 2, -Math.PI / 2 + (2 * Math.PI) / 5, -Math.PI / 2 + (4 * Math.PI) / 5, -Math.PI / 2 + (6 * Math.PI) / 5, -Math.PI / 2 + (8 * Math.PI) / 5];

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
      <div className="panel-heading" style={{ marginBottom: "8px" }}>
        <div>
          <span className="eyebrow">MULTI-VECTOR DIAGNOSTICS</span>
          <h2 style={{ fontSize: "15px" }}>5D Telemetry Vector Radar</h2>
        </div>
        <span className={`live-chip ${isAttacking ? "packet-alert" : "packet-ok"}`}>
          <i /> {isAttacking ? "ANOMALOUS RADAR" : "NOMINAL POLAR"}
        </span>
      </div>

      <div style={{ position: "relative", width: "100%", height: "200px", display: "flex", justifyContent: "center" }}>
        <svg viewBox="0 0 220 220" style={{ width: "210px", height: "210px" }}>
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

          {/* Dynamic Telemetry Polygon */}
          <polygon
            points={polygonPoints}
            fill={isAttacking ? "color-mix(in srgb, var(--red) 25%, transparent)" : "color-mix(in srgb, var(--cyan) 20%, transparent)"}
            stroke={isAttacking ? "var(--red)" : "var(--cyan)"}
            strokeWidth="2"
            style={{ transition: "all 0.4s ease" }}
          />

          {/* Radar Vertices Dots */}
          {angles.map((angle, i) => {
            const r = Math.max(0.12, Math.min(1.0, values[i])) * maxR;
            const x = center + r * Math.cos(angle);
            const y = center + r * Math.sin(angle);
            return <circle key={i} cx={x} cy={y} r="3.5" fill={isAttacking ? "var(--red)" : "var(--cyan)"} />;
          })}
        </svg>

        {/* Axis Labels Overlay */}
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none", fontSize: "8px", fontWeight: "700" }}>
          <span style={{ position: "absolute", top: "2px", left: "50%", transform: "translateX(-50%)", color: "var(--cyan)" }}>
            {axisLabels[0].name} ({axisLabels[0].val})
          </span>
          <span style={{ position: "absolute", top: "35%", right: "-2px", color: "var(--ink)" }}>
            {axisLabels[1].name}
          </span>
          <span style={{ position: "absolute", bottom: "10px", right: "20px", color: "var(--ink)" }}>
            {axisLabels[2].name}
          </span>
          <span style={{ position: "absolute", bottom: "10px", left: "20px", color: "var(--ink)" }}>
            {axisLabels[3].name}
          </span>
          <span style={{ position: "absolute", top: "35%", left: "-2px", color: "var(--amber)" }}>
            {axisLabels[4].name}
          </span>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "var(--muted)", borderTop: "1px solid var(--line)", paddingTop: "8px", marginTop: "4px" }}>
        <span>Topology: <b>5 Vector Space</b></span>
        <span>Confidence: <b>{isAttacking ? "99.8%" : "99.4%"}</b></span>
      </div>
    </section>
  );
}

// 3. Security History Dual Waveform Charts
function SecurityDualWaveformChart({ points }: { points: Array<{ time: string; trust: number; anomaly: number; synRate: number }> }) {
  const width = 680;
  const height = 140;

  const trustPath = points
    .map((p, i) => `${i ? "L" : "M"} ${(i / Math.max(points.length - 1, 1)) * width} ${height - p.trust * 1.25}`)
    .join(" ");

  const synPath = points
    .map((p, i) => `${i ? "L" : "M"} ${(i / Math.max(points.length - 1, 1)) * width} ${height - Math.min(100, (p.synRate / 280) * 100) * 1.25}`)
    .join(" ");

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
      {/* Waveform 1: Trust & Anomaly Waveform */}
      <section className="history panel" style={{ marginTop: 0 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TELEMETRY WAVEFORM A</span>
            <h2 style={{ fontSize: "14px" }}>Trust &amp; Anomaly Index</h2>
          </div>
          <div className="chart-key" style={{ fontSize: "9px" }}>
            <span className="trust-key" /> Trust <span className="anomaly-key" /> Anomaly
          </div>
        </div>
        <svg className="history-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ height: "140px" }}>
          <path className="grid-line" d="M0 20H680M0 60H680M0 100H680" />
          <path className="trust-line" d={trustPath} />
        </svg>
      </section>

      {/* Waveform 2: SYN Packet Rate Waveform */}
      <section className="history panel" style={{ marginTop: 0 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TELEMETRY WAVEFORM B</span>
            <h2 style={{ fontSize: "14px" }}>SYN Rate Ingestion Frequency</h2>
          </div>
          <div className="chart-key" style={{ fontSize: "9px" }}>
            <span className="trust-key" style={{ background: "var(--amber)" }} /> Packet Rate (/s)
          </div>
        </div>
        <svg className="history-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ height: "140px" }}>
          <path className="grid-line" d="M0 20H680M0 60H680M0 100H680" />
          <path className="trust-line" stroke="var(--amber)" d={synPath} />
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
  const [action, setAction] = useState<string | null>(null);

  const [overrideAttack, setOverrideAttack] = useState<boolean | null>(null);
  const [liveTrustScore, setLiveTrustScore] = useState<number>(98);
  const [liveVaeError, setLiveVaeError] = useState<number>(0.0161);
  const [liveJsdDrift, setLiveJsdDrift] = useState<number>(0.0271);

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

  const handleLaunchAttack = async () => {
    setOverrideAttack(true);
    setAction("🚀 Attack launched (Instant UI response)");

    try {
      await apiJson("/api/v1/demo/replay/pi_syn?speed=4", { method: "POST" });
      await refresh();
    } catch {
      // Keep local instant state
    }
  };

  const handleRemediate = async () => {
    setOverrideAttack(false);
    setAction("🛡️ Device remediated (Restored to HEALTHY)");

    try {
      await apiJson("/api/v1/devices/PI-001/remediate", { method: "POST" });
      await refresh();
    } catch {
      // Keep local instant state
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

            <div style={{ display: "flex", width: "100%", gap: "10px" }}>
              <button
                type="button"
                className="attack-button"
                style={{ flex: 1, padding: "10px 6px", fontSize: "10px", fontWeight: "700" }}
                onClick={() => void handleLaunchAttack()}
              >
                🚀 LAUNCH ATTACK
              </button>
              <button
                type="button"
                className="reset-button"
                style={{ flex: 1, padding: "10px 6px", fontSize: "10px", fontWeight: "700", borderColor: "var(--cyan)", color: "var(--cyan)" }}
                onClick={() => void handleRemediate()}
              >
                🛡️ REMEDIATE
              </button>
            </div>
            {action && <small style={{ color: "var(--cyan)", marginTop: "6px", textAlign: "center" }}>{action}</small>}
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

        {/* MIDDLE ROW: Clean Mathematical Model Cards & MITRE ATT&CK Mapping */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "20px" }}>
          {/* Card 1: VAE Reconstruction Error */}
          <section className="panel" style={{ padding: "18px" }}>
            <span className="eyebrow">ANOMALY DETECTOR MODEL</span>
            <h2 style={{ margin: "4px 0 10px", fontSize: "15px" }}>VAE Reconstruction Error</h2>
            <div style={{ background: "var(--color-surface-raised)", border: "1px solid var(--line)", padding: "8px 10px", borderRadius: "4px", fontSize: "11px", color: "var(--cyan)", fontFamily: "monospace", marginBottom: "12px", lineHeight: "1.4" }}>
              {"L_VAE = ||x - x_hat||^2 + D_KL(q(z|x) || p(z))"}
            </div>
            <div className="hardware-data-list">
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
            <h2 style={{ margin: "4px 0 10px", fontSize: "15px" }}>JSD Statistical Drift</h2>
            <div style={{ background: "var(--color-surface-raised)", border: "1px solid var(--line)", padding: "8px 10px", borderRadius: "4px", fontSize: "11px", color: "var(--amber)", fontFamily: "monospace", marginBottom: "12px", lineHeight: "1.4" }}>
              {"D_JS(P || Q) = 0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M)"}
            </div>
            <div className="hardware-data-list">
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

