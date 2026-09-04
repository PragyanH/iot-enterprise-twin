"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";

// Coordinates offset precisely around building footprints to prevent text overlapping
const devicePinCoords: Record<string, { left: string; top: string; icon: string }> = {
  "PI-001": { left: "14%", top: "33%", icon: "📹" },  // A-Block CCTV (Raspberry Pi)
  "DEV-002": { left: "45%", top: "33%", icon: "💧" },  // B-Block Industrial Water Pump
  "DEV-003": { left: "76%", top: "33%", icon: "⛽" },  // C-Block Motor Gas Sensor
  "DEV-004": { left: "14%", top: "79%", icon: "🔐" },  // SVP Block Smart Door Lock
  "DEV-005": { left: "45%", top: "79%", icon: "🖨️" },  // Xerox Shop IoT Printer
  "DEV-006": { left: "67%", top: "79%", icon: "☕" },  // Nescafe Outlet Smoke Detector
  "DEV-007": { left: "91%", top: "25%", icon: "🌡️" },  // Central Library Temp Sensor
  "DEV-008": { left: "91%", top: "42%", icon: "🚨" },  // Central Library Smart Fire Alarm
  "DEV-009": { left: "91%", top: "79%", icon: "📡" },  // Main Security Gate Weather Sensor
};

export function BuildingMap({ devices }: { devices: MockDevice[] }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <section className="map-panel panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">NHCE CAMPUS TELEMETRY · MASTER BLUEPRINT CAD</span>
          <h2>NHCE College Operational Campus Map</h2>
        </div>
        <div className="floor-tabs">
          <span className="active">BLUEPRINT ARCHITECTURE</span>
          <span>BUILDING BLOCKS</span>
          <span>FIBER TELEMETRY BUS</span>
        </div>
      </div>

      <div className="blueprint-map-container">
        {/* CAD Architectural Vector Blueprint Background */}
        <svg viewBox="0 0 1000 600" className="nhce-blueprint-svg" role="img" aria-label="NHCE Campus Master Plan Architectural Blueprint">
          <defs>
            {/* Fine CAD Blueprint Grid */}
            <pattern id="cadGrid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="var(--line)" strokeWidth="0.6" strokeOpacity="0.3" />
            </pattern>

            <pattern id="majorCadGrid" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#cadGrid)" />
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="var(--cyan)" strokeWidth="0.8" strokeOpacity="0.2" />
            </pattern>

            {/* Glowing Fiber Optic Filter */}
            <filter id="neonGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Building Drop Shadow */}
            <filter id="cadShadow" x="-15%" y="-15%" width="130%" height="130%">
              <feDropShadow dx="3" dy="6" stdDeviation="5" floodColor="#000000" floodOpacity="0.4" />
            </filter>

            {/* Linear Gradient for Fiber Optics */}
            <linearGradient id="fiberGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--cyan)" stopOpacity="0.4" />
              <stop offset="50%" stopColor="var(--cyan)" stopOpacity="1" />
              <stop offset="100%" stopColor="var(--cyan)" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Canvas Base Layer */}
          <rect width="1000" height="600" fill="var(--color-surface-raised)" />
          <rect width="1000" height="600" fill="url(#majorCadGrid)" />

          {/* Campus Boundary & Perimeter Fence */}
          <rect x="40" y="30" width="920" height="540" rx="12" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" strokeDasharray="10 5" />
          <text x="50" y="52" fill="var(--color-text-muted)" fontSize="9" fontWeight="800" letterSpacing="0.16em">
            NEW HORIZON COLLEGE OF ENGINEERING · CAMPUS CAD BOUNDARY
          </text>

          {/* North Academic Quad Lawn */}
          <path d="M 60 70 H 940 V 270 H 60 Z" fill="color-mix(in srgb, var(--cyan) 2%, transparent)" stroke="var(--cyan)" strokeWidth="0.8" strokeDasharray="3 3" strokeOpacity="0.3" />
          <text x="70" y="86" fill="var(--cyan)" fontSize="9" fontWeight="800" letterSpacing="0.12em" opacity="0.7">NORTH ACADEMIC QUAD</text>

          {/* South Amenities & Services Zone */}
          <path d="M 60 330 H 940 V 550 H 60 Z" fill="color-mix(in srgb, var(--amber) 2%, transparent)" stroke="var(--amber)" strokeWidth="0.8" strokeDasharray="3 3" strokeOpacity="0.3" />
          <text x="70" y="346" fill="var(--amber)" fontSize="9" fontWeight="800" letterSpacing="0.12em" opacity="0.7">SOUTH AMENITIES &amp; SERVICES ZONE</text>

          {/* Main Campus Boulevard Road & Markings */}
          <g>
            <rect x="40" y="280" width="920" height="40" fill="color-mix(in srgb, var(--color-text) 6%, transparent)" stroke="var(--line)" strokeWidth="1" />
            <line x1="40" y1="300" x2="960" y2="300" stroke="var(--amber)" strokeWidth="1.5" strokeDasharray="16 10" opacity="0.8" />
            <text x="500" y="304" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9" fontWeight="800" letterSpacing="0.22em">MAIN CAMPUS BOULEVARD (ENTRY &amp; EXIT)</text>
          </g>

          {/* Vertical Pedestrian Concourse Pathways */}
          <rect x="300" y="70" width="24" height="480" fill="color-mix(in srgb, var(--color-text) 3%, transparent)" stroke="var(--line)" strokeWidth="0.6" />
          <rect x="580" y="70" width="24" height="480" fill="color-mix(in srgb, var(--color-text) 3%, transparent)" stroke="var(--line)" strokeWidth="0.6" />

          {/* Animated Fiber Optic Telemetry Bus Lines */}
          <g filter="url(#neonGlow)">
            {/* Trunk Bus line 1 */}
            <path d="M 140 180 H 450 H 760 V 300 H 910 V 150" fill="none" stroke="url(#fiberGrad)" strokeWidth="2.5" />
            {/* Trunk Bus line 2 */}
            <path d="M 140 470 H 450 H 670 V 300 H 910 V 470" fill="none" stroke="url(#fiberGrad)" strokeWidth="2.5" />
            
            {/* Animated Fiber Pulses */}
            <circle cx="140" cy="180" r="3.5" fill="var(--cyan)" className="dash-fast" />
            <path d="M 140 180 H 760 V 300 H 910" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeDasharray="8 12" className="dash-fast" />
            <path d="M 140 470 H 670 V 300 H 910" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeDasharray="8 12" className="dash-fast" />
          </g>

          {/* ------------------- ARCHITECTURAL BUILDING FOOTPRINTS ------------------- */}

          {/* 1. A-BLOCK (CSE & IT - PI-001) */}
          <g className="building-group" filter="url(#cadShadow)">
            <path d="M 70 100 H 220 V 220 H 140 V 170 H 70 Z" fill="var(--color-surface)" stroke="var(--cyan)" strokeWidth="2" />
            {/* Roof Blueprint Hatching */}
            <path d="M 70 120 L 90 100 M 70 140 L 110 100 M 70 160 L 130 100 M 70 170 L 140 100 M 100 170 L 160 110 M 140 190 L 170 160" fill="none" stroke="var(--cyan)" strokeWidth="0.8" opacity="0.25" />
            {/* Dept Label Badge */}
            <rect x="78" y="108" width="58" height="20" rx="3" fill="color-mix(in srgb, var(--cyan) 14%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="107" y="122" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">A-BLOCK</text>
            <text x="148" y="145" fill="var(--color-text)" fontSize="11" fontWeight="800">CSE &amp; IT WING</text>
            <text x="148" y="160" fill="var(--color-text-muted)" fontSize="8">Raspberry Pi · CCTV (PI-001)</text>
          </g>

          {/* 2. B-BLOCK (MECHANICAL & CIVIL - DEV-002) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="350" y="100" width="200" height="120" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            {/* Industrial Skylight Windows */}
            <line x1="370" y1="100" x2="370" y2="220" stroke="var(--line)" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="430" y1="100" x2="430" y2="220" stroke="var(--line)" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="490" y1="100" x2="490" y2="220" stroke="var(--line)" strokeWidth="1" strokeDasharray="4 4" />
            
            <rect x="360" y="110" width="180" height="22" rx="3" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="450" y="125" textAnchor="middle" fill="var(--amber)" fontSize="9" fontWeight="800">INDUSTRIAL &amp; MECH BAY</text>
            <text x="450" y="158" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">B-BLOCK ENGINEERING</text>
            <text x="450" y="174" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Civil &amp; Mech · Water Pump</text>
          </g>

          {/* 3. C-BLOCK (EEE & ECE - DEV-003) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="630" y="100" width="180" height="120" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <rect x="640" y="110" width="160" height="22" rx="3" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="720" y="125" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">EEE &amp; ECE RESEARCH LABS</text>
            <text x="720" y="158" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">C-BLOCK WING</text>
            <text x="720" y="174" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Electronics · Gas Sensor</text>
          </g>

          {/* 4. CENTRAL LIBRARY (TEMP & FIRE ALARM - DEV-007 & DEV-008) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="850" y="80" width="100" height="180" rx="8" fill="var(--color-surface)" stroke="var(--cyan)" strokeWidth="2" />
            {/* Library Atrium Dome Blueprint */}
            <circle cx="900" cy="140" r="32" fill="color-mix(in srgb, var(--cyan) 6%, transparent)" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="4 3" />
            <circle cx="900" cy="140" r="18" fill="none" stroke="var(--cyan)" strokeWidth="1.5" />
            <line x1="900" y1="108" x2="900" y2="172" stroke="var(--cyan)" strokeWidth="0.8" />
            <line x1="868" y1="140" x2="932" y2="140" stroke="var(--cyan)" strokeWidth="0.8" />
            
            <text x="900" y="210" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">CENTRAL LIBRARY</text>
            <text x="900" y="226" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Temp &amp; Fire Alarm</text>
          </g>

          {/* 5. SARDAR VALLABHBHAI PATEL (SVP) MAIN BLOCK (SMART LOCK - DEV-004) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="70" y="370" width="230" height="130" rx="8" fill="var(--color-surface)" stroke="var(--cyan)" strokeWidth="2" />
            {/* Grand Portico Columns */}
            <rect x="145" y="358" width="80" height="20" rx="3" fill="var(--color-surface-raised)" stroke="var(--cyan)" strokeWidth="1.5" />
            <line x1="165" y1="358" x2="165" y2="378" stroke="var(--cyan)" strokeWidth="1.5" />
            <line x1="205" y1="358" x2="205" y2="378" stroke="var(--cyan)" strokeWidth="1.5" />
            
            <text x="185" y="372" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">MAIN ENTRANCE PORTICO</text>
            <text x="185" y="420" textAnchor="middle" fill="var(--color-text)" fontSize="12" fontWeight="800">SVP ADMINISTRATIVE BLOCK</text>
            <text x="185" y="438" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Sardar Vallabhbhai Patel · Smart Lock</text>
          </g>

          {/* 6. XEROX SHOP (PRINTER - DEV-005) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="360" y="380" width="170" height="110" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <rect x="370" y="390" width="150" height="20" rx="3" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="445" y="404" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">STUDENT SERVICES HUB</text>
            <text x="445" y="438" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">XEROX SHOP</text>
            <text x="445" y="454" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Reprographics · IoT Printer</text>
          </g>

          {/* 7. NESCAFE OUTLET (SMOKE DETECTOR - DEV-006) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="580" y="380" width="160" height="110" rx="6" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="2" />
            <circle cx="660" cy="410" r="15" fill="color-mix(in srgb, var(--amber) 14%, transparent)" stroke="var(--amber)" strokeWidth="1.5" />
            <text x="660" y="414" textAnchor="middle" fill="var(--amber)" fontSize="10">☕</text>
            <text x="660" y="444" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">NESCAFE OUTLET</text>
            <text x="660" y="460" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Food Court · Smoke Detector</text>
          </g>

          {/* 8. MAIN SECURITY GATE (WEATHER SENSOR - DEV-009) */}
          <g className="building-group" filter="url(#cadShadow)">
            <rect x="850" y="370" width="100" height="130" rx="8" fill="var(--color-surface)" stroke="var(--cyan)" strokeWidth="2" />
            <path d="M 870 370 V 350 H 930 V 370 Z" fill="var(--color-surface-raised)" stroke="var(--cyan)" strokeWidth="1.5" />
            <text x="900" y="363" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">CHECKPOINT</text>
            <text x="900" y="425" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">SECURITY GATE</text>
            <text x="900" y="442" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8">Gatehouse · Weather Sensor</text>
          </g>

          {/* CAD Compass Rose */}
          <g transform="translate(940, 550)">
            <circle cx="0" cy="0" r="18" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <path d="M 0 -14 L 4 0 L 0 4 L -4 0 Z" fill="var(--cyan)" />
            <text x="0" y="-17" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">N</text>
          </g>
        </svg>

        {/* ------------------- GLASSMOROPHISM INTERACTIVE PINS ------------------- */}
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

              {/* Blueprint Glassmorphism Tooltip */}
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

