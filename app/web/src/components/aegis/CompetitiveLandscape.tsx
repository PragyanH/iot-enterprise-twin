"use client";

import { useState } from "react";

type Edge = "research" | "industry";

const researchRows = [
  ["Normal behavior learning", "One-class autoencoder + ensemble", "SSAE representation + XGBoost", "LSTM-VAE + XGBoost"],
  ["Independent evidence channels", "Partial", "Partial", "Rules + XGBoost + LSTM-VAE + JSD"],
  ["Unknown / unmapped state", "Limited by nearest-known classification", "Classifier-oriented", "Preserved explicitly"],
  ["Continuous device trust", "Not central", "Not central", "Core abstraction"],
  ["Operational lifecycle", "Detection and classification", "Detection and classification", "Proof, response and recovery"],
];

const industryRows = [
  ["Primary strength", "Asset intelligence and exposure", "Self-learning AI and response", "OT/IoT visibility and workflows", "Device-centric resilience"],
  ["Behavioral detection", "Yes", "Core strength", "Yes", "Yes"],
  ["Known and unknown behavior", "Yes", "Yes", "Yes", "Yes, separately evidenced"],
  ["Enterprise breadth", "Major", "Major", "Major", "Targeted prototype"],
  ["Per-device trust driving a twin", "Different risk models", "Different AI scoring", "Risk scoring", "Core abstraction"],
  ["Clean-window recovery", "Platform-specific", "Platform-specific", "Workflow-specific", "Explicit state machine"],
];

const stages = ["OBSERVE", "DETECT", "EXPLAIN", "PROVE", "REMEDIATE", "RECOVER", "RE-SYNC"];

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <span className="eyebrow">{children}</span>;
}

function EvidenceChannel({ name, question, detail }: { name: string; question: string; detail: string }) {
  return (
    <article className="poc-evidence-card">
      <strong>{name}</strong>
      <b>{question}</b>
      <p>{detail}</p>
    </article>
  );
}

function ComparisonTable({ rows, industry }: { rows: string[][]; industry?: boolean }) {
  const headings = industry
    ? ["Dimension", "Armis", "Darktrace", "Nozomi", "Aegis-Twin"]
    : ["Dimension", "Yao et al. 2023", "Vinayak & Jarin 2025", "Aegis-Twin"];
  return (
    <div className="poc-table-wrap">
      <table className="poc-table">
        <thead>
          <tr>
            {headings.map((heading) => (
              <th key={heading}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[0]}>
              {row.map((cell, index) => (
                <td className={index === row.length - 1 ? "poc-highlight" : ""} key={`${row[0]}-${cell}`}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvidenceGraphic() {
  return (
    <div className="poc-evidence-graphic" aria-label="Four evidence channels converging into device trust">
      <div className="poc-graphic-channels">
        <div className="poc-channel-chip rules">
          <span className="dot" />
          <span>RULES</span>
        </div>
        <div className="poc-channel-chip xgboost">
          <span className="dot" />
          <span>XGBOOST</span>
        </div>
        <div className="poc-channel-chip lstm">
          <span className="dot" />
          <span>LSTM-VAE</span>
        </div>
        <div className="poc-channel-chip jsd">
          <span className="dot" />
          <span>JSD DRIFT</span>
        </div>
      </div>
      <div className="poc-graphic-lines">
        <i className="laser-pulse p1" />
        <i className="laser-pulse p2" />
        <i className="laser-pulse p3" />
        <i className="laser-pulse p4" />
      </div>
      <div className="poc-graphic-core">
        <div className="core-glow-ring" />
        <b>TRUST</b>
        <small>COMPOSER</small>
      </div>
      <div className="poc-graphic-output-wrapper">
        <div className="output-laser-line" />
        <div className="poc-graphic-output">
          <span className="live-dot" />
          DEVICE STATE
        </div>
      </div>
    </div>
  );
}

function TrustGraphic() {
  return (
    <div className="poc-trust-graphic" aria-label="Trust falls from healthy to attack and recovers after clean windows">
      <div className="poc-chart-labels">
        <span>100</span>
        <span>50</span>
        <span>0</span>
      </div>
      <div className="poc-chart-svg-wrap">
        <svg viewBox="0 0 420 150" role="img" aria-label="Trust trajectory from 98 to 23 to 97">
          <defs>
            <linearGradient id="trustFillGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--cyan)" stopOpacity="0.18" />
              <stop offset="100%" stopColor="var(--cyan)" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="trustLineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--green)" />
              <stop offset="25%" stopColor="var(--green)" />
              <stop offset="45%" stopColor="var(--red)" />
              <stop offset="65%" stopColor="var(--red)" />
              <stop offset="85%" stopColor="var(--green)" />
              <stop offset="100%" stopColor="var(--green)" />
            </linearGradient>
          </defs>
          <path className="poc-chart-grid" d="M0 25H420M0 75H420M0 125H420" />
          {/* Translucent fill under graph curve */}
          <path
            className="poc-chart-area"
            fill="url(#trustFillGrad)"
            d="M12 28 C70 29 96 32 135 56 S190 122 230 120 S300 106 345 72 S385 35 408 30 L408 145 L12 145 Z"
          />
          {/* Main Trajectory Line with Dual-Tone Green/Red/Green Gradient */}
          <path
            className="poc-trust-line"
            stroke="url(#trustLineGrad)"
            d="M12 28 C70 29 96 32 135 56 S190 122 230 120 S300 106 345 72 S385 35 408 30"
          />
          {/* Vertex Node Glow Rings and Circles */}
          <circle cx="12" cy="28" r="8" fill="var(--green)" opacity="0.25" />
          <circle cx="12" cy="28" r="4.5" fill="var(--green)" stroke="var(--color-surface)" strokeWidth="1.5" />

          <circle cx="230" cy="120" r="9" fill="var(--red)" opacity="0.3" className="pulse-circle" />
          <circle cx="230" cy="120" r="5" fill="var(--red)" stroke="var(--color-surface)" strokeWidth="1.5" />

          <circle cx="408" cy="30" r="8" fill="var(--green)" opacity="0.25" />
          <circle cx="408" cy="30" r="4.5" fill="var(--green)" stroke="var(--color-surface)" strokeWidth="1.5" />
        </svg>
        <div className="poc-chart-markers">
          <span className="marker-healthy">
            <b>98</b>
            <small>HEALTHY</small>
          </span>
          <span className="marker-attack">
            <b>23</b>
            <small>ATTACK</small>
          </span>
          <span className="marker-restored">
            <b>97</b>
            <small>RESTORED</small>
          </span>
        </div>
      </div>
    </div>
  );
}

function MarketWedgeGraphic() {
  return (
    <div className="poc-wedge-graphic" aria-label="Aegis positioned for behavioral depth while enterprise platforms provide breadth">
      <div className="wedge-grid-bg">
        <svg className="wedge-grid-svg" viewBox="0 0 400 220">
          <line x1="0" y1="110" x2="400" y2="110" stroke="var(--line)" strokeDasharray="4 4" strokeWidth="1" />
          <line x1="200" y1="0" x2="200" y2="220" stroke="var(--line)" strokeDasharray="4 4" strokeWidth="1" />
          <line x1="40" y1="180" x2="360" y2="40" stroke="var(--cyan)" strokeWidth="1.5" opacity="0.3" strokeDasharray="6 4" />
        </svg>
      </div>
      <div className="poc-axis-y">
        <span>ENTERPRISE BREADTH</span>
        <i>↑</i>
      </div>
      <div className="poc-axis-x">
        <span>BEHAVIORAL DEPTH</span>
        <i>→</i>
      </div>

      <div className="wedge-quadrant q-top-left">Enterprise Visibility</div>
      <div className="wedge-quadrant q-bottom-right">Edge Resilience Wedge</div>

      <div className="poc-market-dot armis">
        <span className="dot-ping" />
        <b>ARMIS</b>
      </div>
      <div className="poc-market-dot darktrace">
        <span className="dot-ping" />
        <b>DARKTRACE</b>
      </div>
      <div className="poc-market-dot nozomi">
        <span className="dot-ping" />
        <b>NOZOMI</b>
      </div>
      <strong className="poc-market-dot aegis">
        <span className="aegis-pulse-glow" />
        <span className="dot-tag">THE WEDGE</span>
        <b>AEGIS-TWIN</b>
      </strong>
    </div>
  );
}

export function CompetitiveLandscape() {
  const [edge, setEdge] = useState<Edge>("research");

  return (
    <section className="landscape-section poc-module">
      <header className="poc-hero">
        <div>
          <SectionLabel>POC · RESEARCH + INDUSTRY POSITIONING</SectionLabel>
          <h2>Why Aegis-Twin exists</h2>
          <p>
            Detection is only the beginning. Aegis explains trust loss, preserves proof, controls response, and verifies recovery for the physical device.
          </p>
        </div>
        <div className="poc-thesis">
          <span>THE WEDGE</span>
          <strong>Explainable resilience for high-value edge devices.</strong>
        </div>
      </header>

      {/* Lifecycle Stage Pills */}
      <div className="poc-lifecycle">
        {stages.map((stage, index) => (
          <div className="poc-stage" key={stage}>
            <b>{String(index + 1).padStart(2, "0")}</b>
            <span>{stage}</span>
            {index < stages.length - 1 && <i>→</i>}
          </div>
        ))}
      </div>

      {/* Modern Neon Segmented Tab Switcher */}
      <div className="poc-tabs-wrapper">
        <div className="poc-tabs" role="tablist" aria-label="POC positioning sections">
          <button
            className={edge === "research" ? "active" : ""}
            onClick={() => setEdge("research")}
            role="tab"
            aria-selected={edge === "research"}
          >
            01 · RESEARCH EDGE
          </button>
          <button
            className={edge === "industry" ? "active" : ""}
            onClick={() => setEdge("industry")}
            role="tab"
            aria-selected={edge === "industry"}
          >
            02 · INDUSTRY EDGE
          </button>
        </div>
      </div>

      {edge === "research" ? (
        <div className="poc-edge-content" role="tabpanel">
          <div className="poc-intro-grid">
            <div>
              <SectionLabel>RESEARCH EDGE</SectionLabel>
              <h3>From alert to explainable trust</h3>
              <p>Existing IDS work classifies traffic. Aegis keeps the reasons visible and carries trust through recovery.</p>
              <EvidenceGraphic />
            </div>
            <div className="poc-quote">
              “Something is wrong”
              <strong>is not the same as</strong>
              “We know exactly what this is.”
            </div>
          </div>

          <div className="poc-section-heading">
            <SectionLabel>FOUR INDEPENDENT CHANNELS</SectionLabel>
            <h3>Evidence remains visible</h3>
          </div>

          <div className="poc-evidence-grid">
            <EvidenceChannel
              name="RULES"
              question="Does traffic satisfy known security knowledge?"
              detail="Deterministic signatures such as high SYN rate, incomplete connections and low handshake completion."
            />
            <EvidenceChannel
              name="XGBOOST"
              question="Which known attack class fits the features?"
              detail="Supervised evidence for known behavior, with the classification kept distinct from anomaly evidence."
            />
            <EvidenceChannel
              name="LSTM-VAE"
              question="Is temporal behavior inconsistent with normal?"
              detail="Sequence reconstruction surfaces unfamiliar device behavior without requiring a known attack label."
            />
            <EvidenceChannel
              name="JSD DRIFT"
              question="Has the distribution shifted?"
              detail="Statistical divergence provides an independent view of feature-distribution change."
            />
          </div>

          <div className="poc-composer">
            <div>
              <SectionLabel>TRUST COMPOSER</SectionLabel>
              <h3>Evidence becomes operational trust</h3>
              <p>Known attacks stay known. Unfamiliar behavior stays unmapped. Trust is restored only after clean windows.</p>
              <TrustGraphic />
            </div>
            <div className="poc-state-stack">
              <span>98 · HEALTHY</span>
              <i>evidence converges</i>
              <strong>23 · ATTACK</strong>
              <i>three clean windows</i>
              <span>97 · RESTORED</span>
            </div>
          </div>

          <div className="poc-section-heading">
            <SectionLabel>RESEARCH COMPARISON</SectionLabel>
            <h3>What Aegis adds to hybrid IDS thinking</h3>
            <p>
              Two published hybrid approaches combine learned representations with classification. Aegis makes the evidence channels independently observable and operational.
            </p>
          </div>

          <ComparisonTable rows={researchRows} />

          <div className="poc-callout">
            <SectionLabel>RESEARCH GAP</SectionLabel>
            <strong>Explainable behavioral trust estimation and cyber-resilience for IoT digital twins.</strong>
            <p>
              The contribution is not simply more models. It is what happens to independently generated evidence: it remains inspectable, drives device trust, and continues through incident creation, forensic capture, controlled remediation and recovery verification.
            </p>
          </div>
        </div>
      ) : (
        <div className="poc-edge-content" role="tabpanel">
          <div className="poc-intro-grid">
            <div>
              <SectionLabel>INDUSTRY EDGE</SectionLabel>
              <h3>A focused wedge beside enterprise platforms</h3>
              <p>Armis, Darktrace and Nozomi validate the market. Aegis focuses on depth of reasoning for one high-value edge device.</p>
              <MarketWedgeGraphic />
            </div>
            <div className="poc-quote">
              “Detecting an attack”
              <strong>is not the end of the story.</strong>
              “Prove the device recovered.”
            </div>
          </div>

          <div className="poc-competitor-grid">
            <article className="competitor-card armis-card">
              <SectionLabel>ARMIS</SectionLabel>
              <h3>Asset intelligence</h3>
              <p>Strong at managed, unmanaged and IoT/OT asset visibility, exposure management, behavioral baselines and enterprise-scale response.</p>
              <b className="card-question-tag">WHAT ASSETS EXIST, AND WHERE IS OUR EXPOSURE?</b>
            </article>
            <article className="competitor-card darktrace-card">
              <SectionLabel>DARKTRACE</SectionLabel>
              <h3>Self-learning defense</h3>
              <p>Strong at self-learning behavior, investigation of known and unknown threats, and targeted autonomous response.</p>
              <b className="card-question-tag">CAN AI LEARN AND INTERVENE AS THREATS EMERGE?</b>
            </article>
            <article className="competitor-card nozomi-card">
              <SectionLabel>NOZOMI</SectionLabel>
              <h3>Industrial visibility</h3>
              <p>Strong at OT/IoT visibility, protocol awareness, behavioral baselines, threat intelligence and operational workflows.</p>
              <b className="card-question-tag">HOW DO WE SECURE A LARGE INDUSTRIAL ESTATE?</b>
            </article>
          </div>

          <ComparisonTable rows={industryRows} industry />

          <div className="poc-depth-grid">
            <div className="depth-intro-card">
              <SectionLabel>AEGIS OPTIMIZES FOR DEPTH</SectionLabel>
              <h3>One device, fully reasoned</h3>
              <p>PI-001 shows the complete path: evidence, trust, incident, response, and verified recovery.</p>
            </div>
            <div className="poc-device-story">
              <div className="story-header-row">
                <span className="story-device-pill">PI-001 · COMPROMISED GATEWAY</span>
                <span className="story-live-chip">LIVE TRAJECTORY</span>
              </div>
              <div className="story-score-row">
                <b>98 → 64 → 23</b>
                <span className="score-badge danger">ATTACK STATE</span>
              </div>
              <small className="story-labels">HEALTHY → SUSPICIOUS → ATTACK</small>
              <em className="story-channels">Rules HIGH · XGBoost SYN_FLOOD · VAE ANOMALOUS · JSD DRIFT</em>
            </div>
          </div>

          <div className="poc-callout">
            <SectionLabel>DEFENSIBLE POSITION</SectionLabel>
            <strong>
              A transparent, device-centric cyber-resilience layer where detection evidence, trust degradation, incident reasoning, remediation and physical recovery are observable as one digital-twin lifecycle.
            </strong>
            <p>
              Enterprise platforms optimize for breadth. Aegis demonstrates a research and prototype wedge below or beside the SOC ecosystem, for industrial controllers, gateways, sensors, cameras and other high-value edge devices.
            </p>
          </div>
        </div>
      )}

      <footer className="poc-footer">
        <span>RESEARCH → PRODUCT</span>
        <b>Rules / XGBoost / LSTM-VAE / JSD → Trust → MITRE → Forensics → Remediation → Clean-window recovery → Twin re-sync</b>
        <strong>Aegis-Twin turns intrusion detection from an alert into an explainable cyber-resilience lifecycle for the physical device.</strong>
      </footer>
    </section>
  );
}

