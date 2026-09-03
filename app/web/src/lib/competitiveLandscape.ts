export type LandscapeId = "ibm" | "kyndryl" | "ecosystem";

export type LandscapeCard = {
  id: LandscapeId;
  eyebrow: string;
  title: string;
  subtitle: string;
  concept: string;
  summary: string;
  detail: string;
  mapping: Array<{ source: string; aegis: string; explanation: string }>;
};

export const landscapeCards: LandscapeCard[] = [
  {
    id: "ibm",
    eyebrow: "Established approach 01",
    title: "IBM / Enterprise cyber resiliency",
    subtitle: "Resilience across complex enterprise infrastructure",
    concept: "ANTICIPATE → WITHSTAND → RECOVER",
    summary: "Enterprise-scale resilience principles across infrastructure such as networks, storage, mainframes, and multi-cloud environments.",
    detail: "Aegis-Twin translates the same resilience lifecycle from enterprise or datacenter scale to the individual IoT device, then adds measurable trust restoration and clean-window verification.",
    mapping: [
      { source: "Enterprise infrastructure", aegis: "Individual IoT device", explanation: "The unit of observation becomes a device-specific behavioral twin." },
      { source: "Detect disruption", aegis: "Detect behavioral deviation", explanation: "Aegis compares each live window with that device's expected behavior." },
      { source: "Contain and recover", aegis: "Contain, verify, restore trust", explanation: "Recovery is evidenced by clean telemetry before the device is trusted again." }
    ]
  },
  {
    id: "kyndryl",
    eyebrow: "Established approach 02",
    title: "Kyndryl / Cyber resilience by design",
    subtitle: "Anticipate → Protect → Withstand → Recover",
    concept: "ANTICIPATE → PROTECT → WITHSTAND → RECOVER",
    summary: "A four-stage resilience framework that provides a clear lens for preparing for, absorbing, and recovering from disruption.",
    detail: "Aegis-Twin applies each resilience phase to a continuously observed device and closes the loop with operational trust and verified recovery.",
    mapping: [
      { source: "ANTICIPATE", aegis: "DIGITAL TWIN / BEHAVIORAL BASELINE", explanation: "Learn what normal looks like for each device before disruption occurs." },
      { source: "PROTECT", aegis: "YAML RULES / POLICY", explanation: "Apply deterministic rules for known signatures and security policy." },
      { source: "WITHSTAND", aegis: "HYBRID DETECTION", explanation: "Use LSTM-VAE, JSD, and classification evidence while the attack is active." },
      { source: "RECOVER", aegis: "REMEDIATE / VERIFY / RESTORE TRUST", explanation: "Contain the registered attack, observe clean windows, and re-synchronize the twin." }
    ]
  },
  {
    id: "ecosystem",
    eyebrow: "Security perspective 03",
    title: "Ecosystem-level security",
    subtitle: "Secure the connected ecosystem, not only one component",
    concept: "IDENTITIES · DATA · APIS · DEPENDENCIES · INFRASTRUCTURE",
    summary: "Modern security thinking treats surrounding identities, data, APIs, dependencies, and infrastructure as part of the security boundary.",
    detail: "Aegis-Twin makes that principle operational at device level: a camera, sensor, alarm, lock, and Pi each receive their own expected behavioral model.",
    mapping: [
      { source: "One global threshold", aegis: "One baseline per device", explanation: "Different device roles are not forced into identical traffic expectations." },
      { source: "Known attack path", aegis: "Known + unknown evidence", explanation: "Rules and XGBoost handle known patterns while LSTM-VAE and JSD surface behavioral drift." },
      { source: "Connected ecosystem", aegis: "Trust Composer → device state", explanation: "Signals become an actionable state for response and recovery." }
    ]
  }
];

export const lifecycleStages = [
  { id: "normal", label: "Normal", title: "Device follows its baseline", text: "PI-001 is operating inside its learned behavioral range.", evidence: "Trust 98 · State HEALTHY" },
  { id: "anomaly", label: "Anomaly", title: "Behavior begins to diverge", text: "LSTM-VAE observes temporal deviation while JSD measures distribution drift.", evidence: "Temporal anomaly HIGH · Drift HIGH" },
  { id: "attack", label: "Attack", title: "Detection signals converge", text: "Known rules and model evidence resolve the event as a SYN FLOOD.", evidence: "Trust 18 · State ATTACK" },
  { id: "classify", label: "Classify", title: "Known behavior is identified", text: "XGBoost and YAML security rules provide complementary evidence.", evidence: "SYN FLOOD · T1498.001" },
  { id: "contain", label: "Contain", title: "Operator authorizes response", text: "The allowlisted controller isolates the path or stops the registered attack job.", evidence: "Human-in-the-loop remediation" },
  { id: "recover", label: "Recover", title: "Clean behavior is verified", text: "Multiple clean telemetry windows are observed before trust is restored.", evidence: "RECOVERING → HEALTHY" },
  { id: "restored", label: "Trust restored", title: "The digital twin re-synchronizes", text: "Trust returns above 95 and the physical and digital states agree.", evidence: "Trust 97 · State HEALTHY" }
];

export const comparisonRows = [
  ["Resilience lifecycle", "Enterprise-scale", "Framework-level", "Device-level"],
  ["Per-device behavioral baseline", "Contextual", "Contextual", "Core capability"],
  ["Known attack detection", "Supported by implementation", "Supported by implementation", "XGBoost + YAML"],
  ["Unknown behavioral deviation", "Depends on implementation", "Depends on implementation", "LSTM-VAE + JSD"],
  ["Operational trust score", "Not the primary abstraction", "Not the primary abstraction", "Core abstraction"],
  ["Allowlisted remediation", "Architecture dependent", "Architecture dependent", "Integrated controller"],
  ["Clean-window verification", "Not the primary focus", "Recovery principle", "Core workflow"],
  ["Digital twin synchronization", "Not the primary abstraction", "Not the primary abstraction", "Core capability"]
];
