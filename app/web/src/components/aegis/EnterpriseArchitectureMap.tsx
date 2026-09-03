"use client";

import { useState } from "react";
import {
  dataFlows,
  firewalls,
  footerColumns,
  legendMarkers,
  remoteActors,
  zones,
  type ZoneNode,
} from "@/lib/enterpriseArchitecture";

function ZoneSection({
  zone,
  selected,
  onSelect,
}: {
  zone: (typeof zones)[number];
  selected: string | undefined;
  onSelect: (node: ZoneNode) => void;
}) {
  return (
    <section className={`enterprise-zone enterprise-zone-${zone.id}`}>
      <div className="enterprise-zone-heading">
        <div>
          <span className="enterprise-zone-label">{zone.label}</span>
          <h3>{zone.title}</h3>
        </div>
        <p>{zone.subtitle}</p>
      </div>
      <div className="enterprise-node-grid">
        {zone.nodes.map((node) => (
          <NodeCard key={node.id} node={node} selected={node.id === selected} onSelect={() => onSelect(node)} />
        ))}
      </div>
    </section>
  );
}

function NodeCard({ node, selected, onSelect }: { node: ZoneNode; selected: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      className={`enterprise-node enterprise-node-${node.marker} ${node.aegis ? "enterprise-node-aegis" : ""} ${selected ? "enterprise-node-selected" : ""}`}
      onClick={onSelect}
      aria-expanded={selected}
    >
      <span className="enterprise-node-marker" aria-hidden="true">
        {legendMarkers.find((entry) => entry.marker === node.marker)?.glyph}
      </span>
      <strong>{node.name}</strong>
      <small>{node.subtitle}</small>
    </button>
  );
}

export function EnterpriseArchitectureMap() {
  const defaultNode = zones.flatMap((zone) => zone.nodes).find((node) => node.id === "aegis-control-plane");
  const [selected, setSelected] = useState<ZoneNode | undefined>(defaultNode);
  const enterpriseZone = zones.find((zone) => zone.id === "enterprise")!;
  const dmzZone = zones.find((zone) => zone.id === "dmz")!;
  const otZone = zones.find((zone) => zone.id === "ot")!;

  return (
    <section className="enterprise-map">
      <div className="enterprise-map-header">
        <div>
          <span className="eyebrow">ENTERPRISE REFERENCE ARCHITECTURE</span>
          <h2>Where Aegis-Twin Fits</h2>
          <p>Reference deployment across enterprise IT, industrial DMZ, and IoT/OT edge security zones.</p>
        </div>
        <span className="source-badge">REFERENCE DEPLOYMENT</span>
      </div>

      <p className="enterprise-map-lede">
        Aegis-Twin operates as an explainable cyber-resilience and incident-orchestration layer between protected
        industrial assets and enterprise security operations.
      </p>

      <div className="enterprise-map-kicker">Three-Zone Industrial Cybersecurity Reference Architecture</div>
      <p className="enterprise-map-kicker-note">
        Purdue-inspired, IEC 62443-aligned segmentation principles — not a certification claim.
      </p>

      <div className="enterprise-map-compare">
        <span>
          <b>CURRENT PHYSICAL DEMO</b>
          <small>Windows + Raspberry Pi + TShark/Npcap + VMware</small>
        </span>
        <span>
          <b>ENTERPRISE REFERENCE DEPLOYMENT</b>
          <small>Load balancer + IAM + SIEM + SOC + XDR/EDR + segmented zones</small>
        </span>
      </div>

      <div className="enterprise-map-diagram">
        <div className="enterprise-remote">
          <div className="remote-actors">
            {remoteActors.map((actor) => (
              <span key={actor}>{actor}</span>
            ))}
          </div>
          <span className="remote-arrow" aria-hidden="true">↓</span>
          <div className="remote-vpn">VPN / Secure Remote Access</div>
        </div>

        <div className="enterprise-firewall">
          <span>{firewalls[0].label}</span>
          <small>{firewalls[0].subtitle}</small>
        </div>

        <ZoneSection zone={enterpriseZone} selected={selected?.id} onSelect={setSelected} />

        <div className="enterprise-firewall">
          <span>{firewalls[1].label}</span>
          <small>{firewalls[1].subtitle}</small>
        </div>

        <ZoneSection zone={dmzZone} selected={selected?.id} onSelect={setSelected} />

        <div className="enterprise-edge-conduit" role="presentation">
          <span className="enterprise-edge-dot" />
          <small>Aegis Control Plane ↕ Aegis Edge Observation · Telemetry / Behavioral Evidence</small>
        </div>

        <div className="enterprise-firewall">
          <span>{firewalls[2].label}</span>
          <small>{firewalls[2].subtitle}</small>
        </div>

        <ZoneSection zone={otZone} selected={selected?.id} onSelect={setSelected} />
      </div>

      {selected && (
        <div className="enterprise-map-detail">
          <div>
            <span className="eyebrow">Selected component</span>
            <h3>{selected.name}</h3>
            <p>{selected.description}</p>
          </div>
          <div className="enterprise-map-detail-note">
            <strong>Aegis complements the existing security stack.</strong>
            <span>Aegis-Twin does not replace SIEM, XDR/EDR, IDS/IPS, or IAM — it adds a device-level behavioral trust and recovery layer.</span>
          </div>
        </div>
      )}

      <div className="enterprise-map-callout">
        <strong>EXPLAINABLE CYBER-RESILIENCE LAYER</strong>
        <span>Observe → Detect → Explain → Prove → Remediate → Recover</span>
      </div>

      <div className="enterprise-map-flows">
        <h3>Major Data Flows</h3>
        <div className="enterprise-flow-grid">
          {dataFlows.map((flow) => (
            <div key={flow.id} className={`enterprise-flow-card flow-${flow.tone}`}>
              <b>{flow.path}</b>
              <small>{flow.label}</small>
            </div>
          ))}
        </div>
      </div>

      <div className="enterprise-map-legend">
        {legendMarkers.map((entry) => (
          <span key={entry.marker}>
            <i aria-hidden="true">{entry.glyph}</i> {entry.label}
          </span>
        ))}
        <span className="enterprise-legend-note">Legend uses shape, not color alone.</span>
      </div>

      <div className="enterprise-map-explain">
        {footerColumns.map((column) => (
          <div key={column.title}>
            <b>{column.title}</b>
            <p>{column.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
