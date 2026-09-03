export type ArchitectureNode = {
  id: string;
  name: string;
  subtitle: string;
  role: string;
  tier: "enterprise" | "dmz" | "ot";
  tone?: "external" | "security" | "aegis" | "system";
};

export const architectureNodes: ArchitectureNode[] = [
  { id: "external", name: "External networks", subtitle: "Internet · users · vendors · cloud", role: "External connectivity enters the enterprise through the perimeter boundary.", tier: "enterprise", tone: "external" },
  { id: "security", name: "Security operations", subtitle: "IDS/IPS · XDR/EDR · SIEM · IAM", role: "Existing enterprise security capabilities collect, correlate, and respond to security events.", tier: "enterprise", tone: "security" },
  { id: "services", name: "Enterprise services", subtitle: "SOC · NOC · Email · ERP · file services", role: "Corporate systems and operations remain part of the broader security ecosystem.", tier: "enterprise", tone: "system" },
  { id: "dmz-services", name: "Application services", subtitle: "VPN · load balancer · reverse proxy", role: "Provides controlled remote access and application delivery inside the DMZ.", tier: "dmz", tone: "system" },
  { id: "app", name: "APP SERVER", subtitle: "Aegis-Twin UI", role: "Presents the operational interface for fleet, device, and trust visibility.", tier: "dmz", tone: "system" },
  { id: "api", name: "API SERVER", subtitle: "FastAPI · Telemetry Window API", role: "Provides controlled application access to normalized telemetry and security state.", tier: "dmz", tone: "system" },
  { id: "database", name: "DATABASE SERVER", subtitle: "Telemetry · models · forensics", role: "Stores application data, model artifacts, and forensic evidence through controlled API access.", tier: "dmz", tone: "system" },
  { id: "aegis", name: "AEGIS-TWIN", subtitle: "Device Trust & Detection Engine", role: "Device-level detection, trust assessment, response, and recovery verification inside the industrial security stack.", tier: "ot", tone: "aegis" },
  { id: "devices", name: "INDUSTRIAL IoT DEVICES", subtitle: "Cameras · sensors · PLCs · robots · HMIs", role: "Connected devices produce the behavior Aegis-Twin models against per-device baselines.", tier: "ot", tone: "system" },
  { id: "control", name: "INDUSTRIAL CONTROL SYSTEMS", subtitle: "SCADA · historian · control servers", role: "Industrial control systems operate alongside the IoT device environment.", tier: "ot", tone: "system" }
];

export const aegisCapabilities = ["Behavioral baseline", "LSTM-VAE anomaly detection", "JSD drift detection", "YAML security rules", "XGBoost classification", "Trust Composer", "Remediation", "Recovery verification"];

export const tierDescriptions = {
  enterprise: "Identity, security operations, enterprise applications, and external connectivity.",
  dmz: "Controlled intermediary zone for applications, APIs, and remote access.",
  ot: "Physical devices and industrial control systems, with Aegis-Twin providing device-level trust intelligence."
};
