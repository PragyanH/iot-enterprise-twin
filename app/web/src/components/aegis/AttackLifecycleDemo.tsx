"use client";

import { useEffect, useMemo, useState } from "react";

type DemoStage = "CONNECTED" | "TELEMETRY" | "HEALTHY" | "ATTACK_STARTED" | "TRAFFIC_CHANGED" | "ANOMALY_DETECTED" | "TRUST_COLLAPSE" | "CLASSIFIED" | "MITRE_MAPPED" | "FORENSICS" | "AWAITING_REMEDIATION" | "REMEDIATING" | "RECOVERY" | "VERIFYING" | "HEALTHY_AGAIN" | "RESYNC";
type FlowStep = { stage: DemoStage; label: string; detail: string; technology: string; purpose: string };

const flow: FlowStep[] = [
  { stage: "CONNECTED", label: "Connect", detail: "Raspberry Pi / PI-001 connected", technology: "Raspberry Pi · PI-001", purpose: "Physical endpoint identity is registered with the digital twin." },
  { stage: "TELEMETRY", label: "Observe", detail: "Live telemetry begins", technology: "Npcap · TShark · tshark_live.py", purpose: "Capture Windows network traffic and normalize one-second telemetry windows." },
  { stage: "HEALTHY", label: "Baseline", detail: "Trust 98 · State HEALTHY", technology: "FastAPI · Telemetry Window API", purpose: "The observed window matches the learned PI-001 baseline." },
  { stage: "ATTACK_STARTED", label: "Attack", detail: "Controlled SYN attack starts", technology: "VMware Linux VM · Scapy · pi-syn-demo", purpose: "The registered attacker generates SYN packets toward PI-001." },
  { stage: "TRAFFIC_CHANGED", label: "Divergence", detail: "Real packet behavior changes", technology: "Aegis Hybrid Engine", purpose: "Packet rate rises while inter-arrival time and handshake symmetry shift." },
  { stage: "ANOMALY_DETECTED", label: "Detect", detail: "Aegis detects divergence", technology: "LSTM-VAE · Jensen-Shannon Divergence", purpose: "Temporal behavior and traffic distributions no longer resemble normal." },
  { stage: "TRUST_COLLAPSE", label: "Decide", detail: "HEALTHY → SUSPICIOUS → ATTACK", technology: "Aegis Trust Composer", purpose: "Temporal anomaly, distribution drift, and known evidence combine into operational risk." },
  { stage: "CLASSIFIED", label: "Classify", detail: "Known attack classified", technology: "XGBoost · YAML Security Rules", purpose: "The known SYN FLOOD signature is matched with high confidence." },
  { stage: "MITRE_MAPPED", label: "Map", detail: "MITRE T1498.001", technology: "MITRE ATT&CK", purpose: "Direct Network Flood is attached to the incident evidence." },
  { stage: "FORENSICS", label: "Prove", detail: "Forensic report created", technology: "Forensic Report Pipeline", purpose: "Incident evidence, scores, windows, and timeline are captured." },
  { stage: "AWAITING_REMEDIATION", label: "Review", detail: "Operator action required", technology: "Human-in-the-loop", purpose: "The demo pauses so the operator can authorize containment." },
  { stage: "REMEDIATING", label: "Contain", detail: "Registered attack job stopped", technology: "Allowlisted Remediation Controller", purpose: "The frontend represents isolation or the guaranteed pi-syn-demo fallback." },
  { stage: "RECOVERY", label: "Recover", detail: "Pi traffic returns to baseline", technology: "Trust / State Engine", purpose: "Traffic gradually settles and the device enters RECOVERING." },
  { stage: "VERIFYING", label: "Verify", detail: "Clean windows verified", technology: "FastAPI · SSE", purpose: "Multiple clean telemetry windows confirm recovery." },
  { stage: "HEALTHY_AGAIN", label: "Restore", detail: "Trust 97 · State HEALTHY", technology: "Aegis Trust Composer", purpose: "Trust returns above 95 only after clean-window verification." },
  { stage: "RESYNC", label: "Re-sync", detail: "Digital twin synchronized", technology: "Aegis Digital Twin", purpose: "Physical and digital state agree again." }
];
const stageIndex = (stage: DemoStage) => flow.findIndex((item) => item.stage === stage);
function stageData(stage: DemoStage, progress: number) {
  const attack = stageIndex(stage) >= stageIndex("ATTACK_STARTED") && stageIndex(stage) < stageIndex("REMEDIATING");
  const recovering = stageIndex(stage) >= stageIndex("RECOVERY");
  const trust = stage === "TRUST_COLLAPSE" ? Math.round(98 - progress * 80) : attack ? 18 : recovering ? Math.round(18 + Math.min(79, progress * 79)) : 98;
  return { attack, recovering, trust: Math.max(18, Math.min(98, trust)), anomaly: attack ? (stage === "TRUST_COLLAPSE" ? Math.min(.94, .2 + progress * .74) : .94) : recovering ? Math.max(.03, .94 - progress * .91) : .02, jsd: attack ? (recovering ? Math.max(.02, .71 - progress * .69) : .71) : .01, packetRate: attack ? 1842 : recovering ? Math.round(1842 - Math.min(1830, progress * 1830)) : 12 };
}

function Metrics({ stage, progress }: { stage: DemoStage; progress: number }) {
  const metrics = stageData(stage, progress);
  return (
    <aside className="xai-metrics-panel">
      <div className="xai-metric-heading">
        <div>
          <span className="eyebrow">LIVE TELEMETRY MONITOR</span>
          <h3>PI-001 BEHAVIOR</h3>
        </div>
        <span className={`xai-live-badge ${metrics.attack ? "badge-attack" : metrics.recovering ? "badge-warning" : "badge-nominal"}`}>
          <i /> {metrics.attack ? "THREAT DETECTED" : metrics.recovering ? "RECOVERING" : "NOMINAL"}
        </span>
      </div>

      <div className="xai-metric-primary">
        <span>Trust Score</span>
        <strong className={metrics.attack ? "metric-danger" : metrics.recovering ? "metric-warning" : "metric-success"}>
          {metrics.trust}
          <small>/100</small>
        </strong>
      </div>

      <div className="xai-metric-chip-row">
        <div className="xai-metric-chip">
          <span>Packet Rate</span>
          <b>{metrics.packetRate.toLocaleString()} <small>/s</small></b>
        </div>
        <div className="xai-metric-chip">
          <span>Anomaly Score</span>
          <b className={metrics.attack ? "text-danger" : ""}>{metrics.anomaly.toFixed(2)}</b>
        </div>
        <div className="xai-metric-chip">
          <span>JSD Drift</span>
          <b className={metrics.attack ? "text-danger" : ""}>{metrics.jsd.toFixed(2)}</b>
        </div>
        <div className="xai-metric-chip">
          <span>Window Size</span>
          <b>1.0 sec</b>
        </div>
      </div>
    </aside>
  );
}

function Architecture({ stage, progress }: { stage: DemoStage; progress: number }) {
  const metrics = stageData(stage, progress);
  const isAttack = metrics.attack;
  return (
    <div className={`xai-pipeline-hero ${isAttack ? "hero-in-attack" : ""}`}>
      <div className="pipeline-hero-header">
        <div>
          <span className="eyebrow">DIGITAL TWIN HARDWARE PIPELINE</span>
          <h3 style={{ margin: "2px 0 0", fontSize: "14px", fontWeight: 700 }}>Real-time Data Stream &amp; Threat Ingestion</h3>
        </div>
        <div className={`pipeline-live-pill ${isAttack ? "pill-attack" : "pill-nominal"}`}>
          <i /> {isAttack ? "SYN FLOOD ATTACK BURST" : "NORMAL TELEMETRY FLOW"}
        </div>
      </div>

      <div className="pipeline-svg-container">
        <svg viewBox="0 0 740 180" className="pipeline-svg" role="img">
          <defs>
            <linearGradient id="normalGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--cyan)" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#00F2FE" stopOpacity="1" />
              <stop offset="100%" stopColor="#4FACFE" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="attackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FF3B5C" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#FF9F43" stopOpacity="0.95" />
            </linearGradient>
            <filter id="cyanGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="redGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Attacker Connection Line to Node 1 (PI-001) */}
          <path
            d="M 590 35 L 110 35 L 110 95"
            fill="none"
            stroke={isAttack ? "var(--red)" : "var(--line)"}
            strokeWidth={isAttack ? "2.5" : "1.5"}
            strokeDasharray={isAttack ? "6 4" : "4 4"}
            className={isAttack ? "dash-fast" : ""}
          />

          {/* Main Pipeline Horizontal Signal Line */}
          <path
            d="M 110 120 H 630"
            fill="none"
            stroke={isAttack ? "url(#attackGrad)" : "url(#normalGrad)"}
            strokeWidth="3.5"
            filter={isAttack ? "url(#redGlow)" : "url(#cyanGlow)"}
          />

          {/* Smooth Traveling Packet Orbs */}
          <g filter={isAttack ? "url(#redGlow)" : "url(#cyanGlow)"}>
            <circle cx="0" cy="0" r={isAttack ? "7" : "5"} fill={isAttack ? "#FF3B5C" : "#00F2FE"}>
              <animateMotion
                path="M 110 120 H 630"
                dur={isAttack ? "1.4s" : "3.8s"}
                repeatCount="indefinite"
              />
            </circle>
            <circle cx="0" cy="0" r={isAttack ? "5.5" : "4"} fill={isAttack ? "#FF9F43" : "#4FACFE"}>
              <animateMotion
                path="M 110 120 H 630"
                dur={isAttack ? "1.4s" : "3.8s"}
                begin={isAttack ? "0.4s" : "1.9s"}
                repeatCount="indefinite"
              />
            </circle>
          </g>

          {isAttack && (
            <circle cx="0" cy="0" r="6" fill="#FF3B5C" filter="url(#redGlow)">
              <animateMotion
                path="M 590 35 L 110 35 L 110 120 H 630"
                dur="1.1s"
                repeatCount="indefinite"
              />
            </circle>
          )}

          {/* ATTACKER NODE (TOP RIGHT) */}
          <g transform="translate(480, 10)" className="hero-node-attacker">
            <rect x="0" y="0" width="220" height="50" rx="8" className={`node-bg-attacker ${isAttack ? "bg-attack-active" : ""}`} />
            <text x="14" y="20" className="hero-tag-amber">⚡ CONTROLLED ATTACKER</text>
            <text x="14" y="38" className="hero-title">VMware Linux VM (Scapy)</text>
            <circle cx="204" cy="25" r="5" fill={isAttack ? "var(--red)" : "var(--muted)"} className={isAttack ? "pulse-red" : ""} />
          </g>

          {/* PIPELINE STAGE 01: Raspberry Pi PI-001 */}
          <g transform="translate(30, 80)" className={`hero-node ${isAttack ? "node-pulse-alert" : ""}`}>
            <rect x="0" y="0" width="140" height="75" rx="8" className="node-bg node-pi" />
            <rect x="12" y="10" width="22" height="16" rx="4" className="badge-bg" />
            <text x="23" y="21" className="badge-txt">01</text>
            <text x="12" y="42" className="hero-node-title">Raspberry Pi</text>
            <text x="12" y="55" className="hero-node-sub">PI-001 (A-Block)</text>
            <text x="12" y="67" className="hero-node-desc">Physical Endpoint</text>
          </g>

          {/* PIPELINE STAGE 02: Capture Layer */}
          <g transform="translate(200, 80)" className="hero-node">
            <rect x="0" y="0" width="140" height="75" rx="8" className="node-bg" />
            <rect x="12" y="10" width="22" height="16" rx="4" className="badge-bg" />
            <text x="23" y="21" className="badge-txt">02</text>
            <text x="12" y="42" className="hero-node-title">Capture Layer</text>
            <text x="12" y="55" className="hero-node-sub">Npcap + TShark</text>
            <text x="12" y="67" className="hero-node-desc">Live Telemetry</text>
          </g>

          {/* PIPELINE STAGE 03: Aegis Hybrid Engine */}
          <g transform="translate(370, 80)" className={`hero-node ${isAttack ? "node-pulse-alert" : "node-pulse-cyan"}`}>
            <rect x="0" y="0" width="150" height="75" rx="8" className="node-bg node-engine" />
            <rect x="12" y="10" width="22" height="16" rx="4" className="badge-bg badge-cyan" />
            <text x="23" y="21" className="badge-txt">03</text>
            <text x="12" y="42" className="hero-node-title">Aegis Engine</text>
            <text x="12" y="55" className="hero-node-sub">FastAPI Hybrid AI</text>
            <text x="12" y="67" className="hero-node-desc">LSTM-VAE + JSD</text>
          </g>

          {/* PIPELINE STAGE 04: Decision & Shield */}
          <g transform="translate(550, 80)" className="hero-node">
            <rect x="0" y="0" width="150" height="75" rx="8" className="node-bg" />
            <rect x="12" y="10" width="22" height="16" rx="4" className="badge-bg" />
            <text x="23" y="21" className="badge-txt">04</text>
            <text x="12" y="42" className="hero-node-title">Decision Layer</text>
            <text x="12" y="55" className="hero-node-sub">XGBoost · MITRE</text>
            <text x="12" y="67" className="hero-node-desc">Forensics &amp; Shield</text>
          </g>
        </svg>
      </div>
    </div>
  );
}

function DetectionEvidence({ stage, progress }: { stage: DemoStage; progress: number }) {
  const metrics = stageData(stage, progress);
  const detection = stageIndex(stage) >= stageIndex("ANOMALY_DETECTED");
  
  return (
    <section className="xai-evidence-panel">
      <div className="xai-section-heading">
        <div>
          <span className="eyebrow">HYBRID EVIDENCE ENGINE</span>
          <h3>Statistical Divergence &amp; Reasoning</h3>
        </div>
        <span className={`evidence-status-pill ${detection ? "pill-alert" : "pill-normal"}`}>
          {detection ? "⚠️ ANOMALY DETECTED" : "✓ BASELINE NOMINAL"}
        </span>
      </div>

      <div className="xai-evidence-cards">
        <div className="xai-calc-card">
          <span className="calc-title">TRAFFIC OBSERVATION WINDOW</span>
          <div className="comparison-flex">
            <div className="calc-col">
              <small>Baseline</small>
              <b>68 B</b>
              <b>420 ms</b>
              <b>0.54</b>
              <b>0.91</b>
            </div>
            <div className="calc-arrow">→</div>
            <div className={`calc-col ${detection ? "col-alert" : ""}`}>
              <small>Observed</small>
              <b>{metrics.attack ? "142 B" : "68 B"}</b>
              <b>{metrics.attack ? "21 ms" : "420 ms"}</b>
              <b>{metrics.attack ? "0.81" : "0.54"}</b>
              <b>{metrics.attack ? "0.42" : "0.91"}</b>
            </div>
          </div>
          <span className="calc-foot">Metrics: Size · Inter-Arrival · Entropy · Symmetry</span>
        </div>

        <div className="xai-calc-card">
          <span className="calc-title">DEVIATION DISTANCE</span>
          <div className="deviation-rows">
            <div className="dev-row"><span>Δ Packet Size:</span> <b className={detection ? "text-danger" : ""}>{metrics.attack ? "+108%" : "+0%"}</b></div>
            <div className="dev-row"><span>Δ Inter-Arrival:</span> <b className={detection ? "text-danger" : ""}>{metrics.attack ? "−95%" : "−0%"}</b></div>
            <div className="dev-row"><span>JSD Divergence:</span> <b className={detection ? "text-danger" : ""}>{metrics.jsd.toFixed(2)}</b></div>
            <div className="dev-row"><span>Temporal Anomaly:</span> <b className={detection ? "text-danger" : ""}>{metrics.anomaly.toFixed(2)}</b></div>
          </div>
        </div>

        <div className="xai-calc-card calc-highlight">
          <span className="calc-title">TRUST COMPOSER OUTPUT</span>
          <div className="composer-rows">
            <div className="comp-row"><span>LSTM-VAE Score:</span> <b>{metrics.anomaly.toFixed(2)}</b></div>
            <div className="comp-row"><span>JSD Drift:</span> <b>{metrics.jsd.toFixed(2)}</b></div>
            <div className="comp-row"><span>YAML Match:</span> <b>{detection ? "SYN FLOOD" : "NONE"}</b></div>
            <div className="comp-trust-box">
              <span>Trust Index</span>
              <strong className={metrics.attack ? "text-danger" : "text-success"}>{metrics.trust}/100</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TechnologyPanel({ current }: { current: FlowStep }) {
  return (
    <section className="xai-tech-card">
      <span className="eyebrow">STAGE INTELLIGENCE</span>
      <h3>{current.technology}</h3>
      <p>{current.purpose}</p>
      <div className="xai-output-box">
        <span>CURRENT STAGE OUTPUT</span>
        <strong>{current.detail}</strong>
      </div>
    </section>
  );
}

export function AttackLifecycleDemo() {
  const [stage, setStage] = useState<DemoStage>("CONNECTED");
  const [progress, setProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const current = flow.find((item) => item.stage === stage) ?? flow[0];
  const canAdvance = stage !== "AWAITING_REMEDIATION" && stage !== "RESYNC";

  const reset = () => {
    setStage("CONNECTED");
    setProgress(0);
    setRunning(false);
  };

  useEffect(() => {
    if (!running || !canAdvance) return;
    const timer = window.setInterval(() => {
      setProgress((value) => {
        if (value < 1) return Math.min(1, value + 0.08);
        const next = flow[stageIndex(stage) + 1];
        if (next) setStage(next.stage);
        return 0;
      });
    }, 260);
    return () => window.clearInterval(timer);
  }, [running, stage, canAdvance]);

  const start = () => {
    if (stage === "RESYNC") reset();
    setRunning(true);
  };

  const remediate = () => {
    if (stage === "AWAITING_REMEDIATION") {
      setStage("REMEDIATING");
      setProgress(0);
      setRunning(true);
    }
  };

  const status = useMemo(() => (stage === "RESYNC" ? "DIGITAL TWIN RE-SYNCHRONIZED" : current.detail), [stage, current.detail]);

  return (
    <section className="xai-demo-wrapper">
      {/* Header Bar */}
      <div className="xai-header-bar">
        <div>
          <span className="eyebrow">EXPLAINABLE AI LAB · LIVE DEMONSTRATION</span>
          <h2>Deterministic Attack &amp; AI Reasoning Lifecycle</h2>
          <p>Inspect real-time physical evidence at PI-001 and trace how Aegis-Twin detects, classifies, and remediates threats.</p>
        </div>
        <div className="xai-header-actions">
          <span className={`xai-status-pill ${stage === "AWAITING_REMEDIATION" ? "pill-danger" : "pill-nominal"}`}>
            <i /> {status}
          </span>
          {stage === "AWAITING_REMEDIATION" ? (
            <button className="xai-action-btn btn-remediate" onClick={remediate}>
              🛡️ CONTAIN &amp; REMEDIATE
            </button>
          ) : (
            <button className="xai-action-btn btn-run" onClick={start}>
              {stage === "RESYNC" ? "🔄 REPLAY DEMONSTRATION" : running ? "⚡ DEMONSTRATION RUNNING" : "🚀 RUN DEMONSTRATION"}
            </button>
          )}
        </div>
      </div>

      {/* Modern Horizontal Timeline Track */}
      <div className="xai-timeline-track">
        {flow.map((item, index) => {
          const isComplete = index < stageIndex(stage);
          const isCurrent = item.stage === stage;
          return (
            <div
              key={item.stage}
              className={`xai-track-step ${isComplete ? "step-complete" : ""} ${isCurrent ? "step-current" : ""}`}
            >
              <div className="step-circle">
                {isComplete ? "✓" : String(index + 1).padStart(2, "0")}
              </div>
              <span className="step-label">{item.label}</span>
            </div>
          );
        })}
      </div>

      {/* Main Row: Architecture & Live Metrics */}
      <div className="xai-top-row">
        <Architecture stage={stage} progress={progress} />
        <Metrics stage={stage} progress={progress} />
      </div>

      {/* Bottom Row: Evidence Calculation & Active Tech */}
      <div className="xai-bottom-row">
        <DetectionEvidence stage={stage} progress={progress} />
        <TechnologyPanel current={current} />
      </div>

      {/* Footer Incident Context Banner */}
      <div className="xai-scenario-footer">
        <span className="eyebrow">SCENARIO SPECIFICATION</span>
        <strong>PI-001 (A-Block CCTV) + VMware Linux VM + SYN FLOOD ATTACK</strong>
        <span className="scenario-detail">
          {stageIndex(stage) >= stageIndex("CLASSIFIED")
            ? "⚡ MITRE ATT&CK T1498.001 · Direct Network Flood Verified"
            : "Baseline telemetry active. Attack signatures will populate upon anomaly detection."}
        </span>
      </div>
    </section>
  );
}