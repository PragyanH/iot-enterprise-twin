"use client";

export function EnterpriseArchitectureMap() {
  return (
    <section className="topology-mesh-container">
      {/* Header Bar */}
      <div className="mesh-header" style={{ marginBottom: "20px" }}>
        <div className="mesh-title-block">
          <div className="mesh-eyebrow-row">
            <span className="mesh-eyebrow">INDUSTRIAL DEPLOYMENT TOPOLOGY MAP</span>
            <span className="mesh-badge">REFERENCE ARCHITECTURE</span>
          </div>
          <h2 className="mesh-main-title">Where Aegis-Twin Fits in the Industrial Landscape</h2>
          <p className="mesh-subtitle">
            Enterprise Industrial IoT / OT network topology map illustrating perimeter security boundaries, DMZ services, field OT controls, and non-intrusive Aegis-Twin detection &amp; trust placement.
          </p>
        </div>
      </div>

      {/* Integration Statement Banner */}
      <div className="mesh-banner" style={{ marginBottom: "20px" }}>
        <span className="mesh-banner-icon">ℹ️</span>
        <div className="mesh-banner-text">
          <strong>NON-INTRUSIVE INTELLIGENCE MEMBRANE:</strong> Aegis-Twin does not replace network switches, firewalls, SIEM, or SOC operations. It attaches over IIoT telemetry channels to transform raw packet streams into explainable trust insights.
        </div>
      </div>

      {/* Industrial Network Environment Diagram View */}
      <div
        className="mesh-canvas"
        style={{
          padding: "16px",
          background: "var(--color-surface-raised)",
          border: "1px solid var(--line)",
          borderRadius: "6px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "auto",
        }}
      >
        <img
          src="/industrial_topology_diagram.jpg"
          alt="Where Aegis-Twin Fits in the Industrial Landscape - Network Topology Map"
          style={{
            width: "100%",
            height: "auto",
            maxHeight: "820px",
            objectFit: "contain",
            borderRadius: "4px",
            boxShadow: "0 6px 24px var(--color-shadow)",
          }}
        />
      </div>

      {/* Legend Footer */}
      <div className="mesh-legend-strip" style={{ marginTop: "20px" }}>
        <span className="legend-title">TOPOLOGY LEGEND:</span>
        <div className="legend-item"><span className="dot cat-physical" /> Physical Assets &amp; Field IoT</div>
        <div className="legend-item"><span className="dot cat-network" /> Firewalls &amp; DMZ Relays</div>
        <div className="legend-item"><span className="dot cat-security_ops" /> SOC / NOC / SIEM Operations</div>
        <div className="legend-item"><span className="dot cat-aegis" /> Aegis-Twin Detection &amp; Trust Engine</div>
      </div>
    </section>
  );
}