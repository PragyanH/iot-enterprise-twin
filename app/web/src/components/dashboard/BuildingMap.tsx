"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";

// Precise coordinates mapped directly onto the master blueprint buildings
const devicePinCoords: Record<string, { left: string; top: string; icon: string }> = {
  "PI-001": { left: "19%", top: "24%", icon: "📹" },  // A-Block CCTV (Raspberry Pi)
  "DEV-002": { left: "44%", top: "24%", icon: "💧" },  // B-Block Industrial Water Pump
  "DEV-003": { left: "69%", top: "24%", icon: "⛽" },  // C-Block Motor Gas Sensor
  "DEV-004": { left: "21%", top: "66%", icon: "🔐" },  // SVP Block Smart Door Lock
  "DEV-005": { left: "45%", top: "68%", icon: "🖨️" },  // Xerox Shop IoT Printer
  "DEV-006": { left: "67%", top: "68%", icon: "☕" },  // Nescafe Outlet Smoke Detector
  "DEV-007": { left: "85%", top: "22%", icon: "🌡️" },  // Central Library Temp Sensor
  "DEV-008": { left: "85%", top: "37%", icon: "🚨" },  // Central Library Smart Fire Alarm
  "DEV-009": { left: "85%", top: "72%", icon: "📡" },  // Main Security Gate Weather Sensor
};

export function BuildingMap({ devices }: { devices: MockDevice[] }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <section className="map-panel panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">NHCE CAMPUS TELEMETRY · MASTER BLUEPRINT</span>
          <h2>NHCE College Operational Campus Map</h2>
        </div>
        <div className="floor-tabs">
          <span className="active">CAMPUS MASTER PLAN</span>
          <span>BUILDING BLOCKS</span>
          <span>IOT SENSOR NODES</span>
        </div>
      </div>

      <div className="blueprint-map-container">
        {/* Vector Architectural Master Blueprint Background */}
        <svg viewBox="0 0 1000 560" className="nhce-blueprint-svg" role="img" aria-label="NHCE Campus Master Plan Blueprint">
          <defs>
            {/* Grid Pattern for Architectural Blueprint feel */}
            <pattern id="blueprintGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--line)" strokeWidth="0.8" strokeOpacity="0.4" />
            </pattern>
            {/* Soft Shadow for Buildings */}
            <filter id="buildingShadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="2" dy="4" stdDeviation="4" floodColor="#000" floodOpacity="0.35" />
            </filter>
            {/* Telemetry Bus Glow */}
            <filter id="busGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Canvas Background Grid */}
          <rect width="1000" height="560" fill="var(--color-surface-raised)" />
          <rect width="1000" height="560" fill="url(#blueprintGrid)" />

          {/* Campus Grounds & Green Lawns */}
          <path d="M 60 40 H 940 V 520 H 60 Z" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
          
          {/* North Quad Lawn */}
          <rect x="80" y="60" width="840" height="190" rx="12" fill="color-mix(in srgb, var(--green) 3%, transparent)" stroke="var(--green)" strokeWidth="0.8" strokeDasharray="4 4" strokeOpacity="0.4" />
          <text x="92" y="78" fill="var(--color-text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.12em">NORTH ACADEMIC QUAD</text>

          {/* South Quad Lawn */}
          <rect x="80" y="300" width="840" height="190" rx="12" fill="color-mix(in srgb, var(--cyan) 3%, transparent)" stroke="var(--cyan)" strokeWidth="0.8" strokeDasharray="4 4" strokeOpacity="0.4" />
          <text x="92" y="318" fill="var(--color-text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.12em">SOUTH AMENITIES &amp; SERVICES ZONE</text>

          {/* Campus Roads & Pathways */}
          {/* Main Horizontal Boulevard */}
          <rect x="60" y="255" width="880" height="40" fill="color-mix(in srgb, var(--color-text) 5%, transparent)" stroke="var(--line)" strokeWidth="1" />
          <line x1="60" y1="275" x2="940" y2="275" stroke="var(--amber)" strokeWidth="1.5" strokeDasharray="12 8" strokeOpacity="0.6" />
          <text x="500" y="279" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.16em">MAIN CAMPUS BOULEVARD</text>

          {/* Vertical Connecting Avenues */}
          <rect x="300" y="60" width="30" height="430" fill="color-mix(in srgb, var(--color-text) 4%, transparent)" stroke="var(--line)" strokeWidth="0.8" />
          <rect x="560" y="60" width="30" height="430" fill="color-mix(in srgb, var(--color-text) 4%, transparent)" stroke="var(--line)" strokeWidth="0.8" />

          {/* Glowing IoT Fiber Telemetry Bus Lines */}
          <g filter="url(#busGlow)">
            <path d="M 190 135 H 440 H 690 V 275 H 850 V 120" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeDasharray="6 4" opacity="0.85" />
            <path d="M 210 370 H 450 H 670 V 275 H 850 V 400" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeDasharray="6 4" opacity="0.85" />
          </g>

          {/* ------------------- BUILDING FOOTPRINTS ------------------- */}

          {/* 1. A-BLOCK (CCTV CAMERA - PI-001) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <path d="M 90 90 H 260 V 180 H 160 V 140 H 90 Z" fill="var(--color-surface)" stroke="var(--color-primary)" strokeWidth="2" />
            <rect x="98" y="98" width="54" height="34" rx="3" fill="color-mix(in srgb, var(--cyan) 10%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="125" y="119" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">A-BLOCK</text>
            <text x="175" y="125" fill="var(--color-text)" fontSize="11" fontWeight="800">A-BLOCK WING</text>
            <text x="175" y="140" fill="var(--color-text-muted)" fontSize="9">CSE &amp; IT Dept · CCTV (PI-001)</text>
          </g>

          {/* 2. B-BLOCK (INDUSTRIAL WATER PUMP - DEV-002) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="350" y="90" width="180" height="90" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <rect x="360" y="100" width="160" height="24" rx="3" fill="color-mix(in srgb, var(--amber) 10%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="440" y="116" textAnchor="middle" fill="var(--amber)" fontSize="9" fontWeight="800">INDUSTRIAL BAY</text>
            <text x="440" y="145" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">B-BLOCK ENGINEERING</text>
            <text x="440" y="160" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Mech &amp; Civil · Water Pump</text>
          </g>

          {/* 3. C-BLOCK (MOTOR GAS SENSOR - DEV-003) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="610" y="90" width="160" height="90" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <rect x="620" y="100" width="140" height="24" rx="3" fill="color-mix(in srgb, var(--cyan) 10%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="690" y="116" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">EEE &amp; ECE LABS</text>
            <text x="690" y="145" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">C-BLOCK WING</text>
            <text x="690" y="160" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Electronics · Motor Gas Sensor</text>
          </g>

          {/* 4. CENTRAL LIBRARY (TEMP & FIRE ALARM - DEV-007 & DEV-008) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="800" y="70" width="120" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-primary)" strokeWidth="2" />
            {/* Library Reading Dome Graphic */}
            <circle cx="860" cy="120" r="28" fill="color-mix(in srgb, var(--cyan) 8%, transparent)" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="3 3" />
            <circle cx="860" cy="120" r="14" fill="none" stroke="var(--cyan)" strokeWidth="1.5" />
            <text x="860" y="180" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">CENTRAL LIBRARY</text>
            <text x="860" y="195" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Temp Sensor &amp; Fire Alarm</text>
          </g>

          {/* 5. SARDAR VALLABHBHAI PATEL (SVP) MAIN BLOCK (SMART LOCK - DEV-004) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="90" y="330" width="240" height="110" rx="8" fill="var(--color-surface)" stroke="var(--color-primary)" strokeWidth="2" />
            {/* Portico Entrance Pillars */}
            <rect x="170" y="322" width="80" height="16" rx="3" fill="var(--color-surface-raised)" stroke="var(--color-primary)" strokeWidth="1.5" />
            <text x="210" y="334" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">MAIN ENTRANCE</text>
            <text x="210" y="375" textAnchor="middle" fill="var(--color-text)" fontSize="12" fontWeight="800">SVP ADMINISTRATIVE BLOCK</text>
            <text x="210" y="392" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Sardar Vallabhbhai Patel Block · Smart Lock</text>
          </g>

          {/* 6. XEROX SHOP (PRINTER - DEV-005) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="370" y="340" width="150" height="90" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <rect x="380" y="350" width="130" height="20" rx="3" fill="color-mix(in srgb, var(--amber) 10%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="445" y="364" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">SERVICES HUB</text>
            <text x="445" y="392" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">XEROX SHOP</text>
            <text x="445" y="407" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Reprographics · IoT Printer</text>
          </g>

          {/* 7. NESCAFE OUTLET (SMOKE DETECTOR - DEV-006) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="590" y="340" width="140" height="90" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <circle cx="660" cy="370" r="14" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1.5" />
            <text x="660" y="374" textAnchor="middle" fill="var(--amber)" fontSize="11">☕</text>
            <text x="660" y="402" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">NESCAFE OUTLET</text>
            <text x="660" y="416" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Food Court · Smoke Detector</text>
          </g>

          {/* 8. MAIN SECURITY GATE (WEATHER SENSOR - DEV-009) */}
          <g className="building-group" filter="url(#buildingShadow)">
            <rect x="800" y="330" width="120" height="120" rx="8" fill="var(--color-surface)" stroke="var(--color-primary)" strokeWidth="2" />
            <path d="M 830 330 V 310 H 890 V 330 Z" fill="var(--color-surface-raised)" stroke="var(--color-primary)" strokeWidth="1.5" />
            <text x="860" y="324" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">GATEHOUSE</text>
            <text x="860" y="380" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">MAIN SECURITY GATE</text>
            <text x="860" y="396" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Checkpoint · Weather Sensor</text>
          </g>

          {/* Campus Orientation Compass */}
          <g transform="translate(930, 500)">
            <circle cx="0" cy="0" r="16" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <path d="M 0 -12 L 4 0 L 0 3 L -4 0 Z" fill="var(--cyan)" />
            <text x="0" y="-15" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">N</text>
          </g>
        </svg>

        {/* ------------------- INTERACTIVE DYNAMIC PINS ------------------- */}
        {devices.map((device) => {
          const pin = devicePinCoords[device.id] ?? { left: "50%", top: "50%", icon: "📍" };
          const href = device.id === "PI-001" ? "/dashboard/hardware/pi-001" : `/dashboard/device/${device.id}`;
          const isHovered = hoveredId === device.id;

          return (
            <Link
              key={device.id}
              href={href}
              className={`blueprint-pin pin-status-${device.status} ${isHovered ? "pin-hovered" : ""}`}
              style={{ left: pin.left, top: pin.top }}
              onMouseEnter={() => setHoveredId(device.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <div className="pin-head">
                <span className="pin-icon">{pin.icon}</span>
                <span className="pin-pulse" />
              </div>
              <div className="pin-tag">
                <b>{device.id}</b>
              </div>

              {/* Rich Blueprint Tooltip */}
              <div className="blueprint-tooltip">
                <div className="tooltip-header">
                  <span className="tooltip-id">{device.id}</span>
                  <span className={`tooltip-badge badge-${device.status}`}>{device.status.toUpperCase()}</span>
                </div>
                <strong>{device.name}</strong>
                <small className="tooltip-location">📍 {device.location}</small>
                <div className="tooltip-meta">
                  <span>Trust: <b>{device.trustScore}/100</b></span>
                  <span>Sensor: <b>{device.type}</b></span>
                </div>
                <span className="tooltip-cta">INSPECT TELEMETRY &amp; REMEDIATION →</span>
              </div>
            </Link>
          );
        })}

        {/* Blueprint Map Legend */}
        <div className="blueprint-map-legend">
          <div className="legend-item"><i className="leg-dot leg-healthy" /> Nominal Device</div>
          <div className="legend-item"><i className="leg-dot leg-warning" /> Telemetry Anomaly</div>
          <div className="legend-item"><i className="leg-dot leg-critical" /> Cyber Attack Active</div>
          <div className="legend-item"><i className="leg-line-bus" /> Fiber Telemetry Bus</div>
        </div>
      </div>
    </section>
  );
}
