export type NodeMarker = "asset" | "platform" | "infra";

export type ZoneNode = {
  id: string;
  name: string;
  subtitle: string;
  description: string;
  marker: NodeMarker;
  aegis?: boolean;
};

export type Zone = {
  id: "enterprise" | "dmz" | "ot";
  label: string;
  title: string;
  subtitle: string;
  nodes: ZoneNode[];
};

export const zones: Zone[] = [
  {
    id: "enterprise",
    label: "ZONE 1",
    title: "Enterprise / IT Security Zone",
    subtitle: "Identity, security operations, and enterprise-facing services",
    nodes: [
      {
        id: "load-balancer",
        name: "Load Balancer",
        subtitle: "Enterprise-facing ingress",
        description: "Distributes authenticated operator traffic across Aegis Web/API replicas. Production deployment option — the current demo runs a single instance.",
        marker: "infra",
      },
      {
        id: "aegis-web",
        name: "Aegis Web",
        subtitle: "Operator UI",
        description: "Enterprise-facing Aegis-Twin application surface used by SOC operators, asset owners, and vendors after authentication.",
        marker: "platform",
        aegis: true,
      },
      {
        id: "iam",
        name: "IAM",
        subtitle: "Identity & Access Management",
        description: "Authenticates and authorizes Admin, Asset Owner, and SME/Vendor roles before any Aegis Control Plane access. Never connects directly to IoT telemetry.",
        marker: "platform",
      },
      {
        id: "siem",
        name: "SIEM",
        subtitle: "Security Information & Event Management",
        description: "Consumes enriched alerts, evidence, and incident context that Aegis produces — Aegis does not replace SIEM correlation.",
        marker: "platform",
      },
      {
        id: "soc",
        name: "SOC",
        subtitle: "Security Operations Center",
        description: "Receives incidents, MITRE mapping, forensics, trust state, and remediation/recovery status from the Aegis Control Plane for explainable decisions.",
        marker: "platform",
      },
      {
        id: "noc",
        name: "NOC",
        subtitle: "Network Operations Center",
        description: "Receives asset state, network health, availability, and recovery status. Security investigation stays centered in the SOC.",
        marker: "platform",
      },
      {
        id: "xdr-edr",
        name: "XDR / EDR",
        subtitle: "Endpoint detection & response",
        description: "Complementary endpoint/threat intelligence exchanged with Aegis. Aegis does not replace XDR/EDR.",
        marker: "platform",
      },
      {
        id: "database",
        name: "Security Database",
        subtitle: "Telemetry, models, forensic evidence",
        description: "Reached only from the Aegis control plane / application layer — no direct external or internet ingress.",
        marker: "infra",
      },
    ],
  },
  {
    id: "dmz",
    label: "ZONE 2",
    title: "Industrial DMZ",
    subtitle: "Controlled boundary between enterprise IT and the OT/IoT edge",
    nodes: [
      {
        id: "aegis-gateway",
        name: "Aegis API Gateway",
        subtitle: "Application gateway / reverse proxy",
        description: "The Aegis server-side bridge: terminates enterprise-side API traffic and forwards normalized telemetry/control calls toward the control plane.",
        marker: "platform",
        aegis: true,
      },
      {
        id: "aegis-control-plane",
        name: "Aegis Control Plane",
        subtitle: "Hybrid Evidence Engine · Rules · XGBoost · LSTM-VAE · JSD · Trust Composer",
        description: "Hybrid detection, trust engine, incident orchestration, MITRE mapping, forensics, remediation control, and recovery verification.",
        marker: "platform",
        aegis: true,
      },
      {
        id: "forensics",
        name: "Forensic Report Service",
        subtitle: "Incident / notification service",
        description: "Generates and stores frozen forensic snapshots and reports, and routes incident notifications toward SOC/assigned SME.",
        marker: "platform",
      },
      {
        id: "log-relay",
        name: "Security Log Relay",
        subtitle: "DMZ data relay",
        description: "Relays security-relevant logs and evidence from the DMZ toward enterprise SIEM without exposing OT devices directly.",
        marker: "infra",
      },
      {
        id: "ids-ips",
        name: "IDS / IPS",
        subtitle: "Network security control",
        description: "Independent network-layer detection/prevention control and evidence source. Observation (Npcap/TShark) is not an IDS/IPS — this is a separate control.",
        marker: "platform",
      },
    ],
  },
  {
    id: "ot",
    label: "ZONE 3",
    title: "OT / IoT / Edge Zone",
    subtitle: "Protected industrial assets and the physical finals demo topology",
    nodes: [
      {
        id: "edge-switch",
        name: "Industrial Switch",
        subtitle: "Edge network",
        description: "Local switched network carrying OT/IoT device traffic to the Aegis Edge observation point.",
        marker: "infra",
      },
      {
        id: "aegis-edge",
        name: "Aegis Edge Observation",
        subtitle: "Npcap / TShark · telemetry normalization",
        description: "Passive packet observation and per-device baseline/behavioral-twin telemetry normalization. Observation only — not a network enforcement control.",
        marker: "platform",
        aegis: true,
      },
      {
        id: "pi-001",
        name: "Raspberry Pi — PI-001",
        subtitle: "Finals hardware asset",
        description: "The physical finals demo endpoint. Labelled as a finals hardware asset, not \"live\", until physical hardware capture is verified.",
        marker: "asset",
      },
      {
        id: "iot-gateway",
        name: "Industrial IoT Gateway",
        subtitle: "Protocol bridge",
        description: "Bridges field-level IoT sensor protocols onto the industrial network segment.",
        marker: "infra",
      },
      {
        id: "iot-sensors",
        name: "IoT Sensors",
        subtitle: "Field devices",
        description: "Representative protected field sensors reporting through the industrial switch.",
        marker: "asset",
      },
      {
        id: "camera",
        name: "Security Camera",
        subtitle: "OT/IoT asset",
        description: "Representative protected OT/IoT video asset.",
        marker: "asset",
      },
      {
        id: "plc",
        name: "PLC / Controller",
        subtitle: "Industrial control asset",
        description: "Representative protected programmable logic controller / industrial control asset.",
        marker: "asset",
      },
    ],
  },
];

export type Firewall = {
  id: string;
  label: string;
  subtitle: string;
};

export const firewalls: Firewall[] = [
  { id: "fw1", label: "FIREWALL 01", subtitle: "External / Remote Access Boundary" },
  { id: "fw2", label: "FIREWALL 02", subtitle: "Enterprise ↔ Industrial DMZ Boundary" },
  { id: "fw3", label: "FIREWALL 03", subtitle: "Industrial DMZ ↔ OT/IoT Boundary" },
];

export type DataFlow = {
  id: string;
  path: string;
  label: string;
  tone: "telemetry" | "intelligence" | "identity" | "response" | "forensic" | "recovery";
};

export const dataFlows: DataFlow[] = [
  { id: "telemetry", path: "IoT / OT Assets → Aegis Edge → Aegis Control Plane", label: "Telemetry / Behavioral Evidence", tone: "telemetry" },
  { id: "intelligence", path: "Aegis Control Plane → SIEM → SOC", label: "Alert · Evidence · Context", tone: "intelligence" },
  { id: "identity", path: "IAM → Aegis Control Plane", label: "Authentication / RBAC", tone: "identity" },
  { id: "response", path: "SOC / Aegis → Controlled Remediation → Network Path", label: "Containment / Remediation", tone: "response" },
  { id: "forensic", path: "Aegis → Forensic Storage & Reporting → SOC / Assigned SME", label: "Forensic Record", tone: "forensic" },
  { id: "recovery", path: "IoT Device → Aegis → SOC", label: "Verified Recovery", tone: "recovery" },
];

export const legendMarkers: { marker: NodeMarker; glyph: string; label: string }[] = [
  { marker: "asset", glyph: "●", label: "Live / protected asset" },
  { marker: "platform", glyph: "▣", label: "Security platform" },
  { marker: "infra", glyph: "▰", label: "Infrastructure" },
];

export const remoteActors = ["Remote Administrator", "Asset Owner", "Authorized Vendor / SME"];

export const footerColumns = [
  {
    title: "Observe at the Edge",
    body: "Aegis receives device-specific network behavior without replacing existing OT infrastructure.",
  },
  {
    title: "Correlate and Explain",
    body: "Hybrid evidence is transformed into explainable trust, incidents, MITRE context and forensic records.",
  },
  {
    title: "Orchestrate Recovery",
    body: "Security operations receive actionable evidence while Aegis verifies that the protected asset returns to a trusted behavioral state.",
  },
];
