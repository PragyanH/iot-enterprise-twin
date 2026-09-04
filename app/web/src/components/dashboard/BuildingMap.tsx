"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";

// Dedicated clean coordinates matching building card top-right headers
const devicePinCoords: Record<string, { left: string; top: string; icon: string }> = {
  "PI-001": { left: "215px", top: "105px", icon: "📹" },  // A-Block CSE & IT (Top-right header)
  "DEV-002": { left: "515px", top: "105px", icon: "💧" },  // B-Block Engineering (Top-right header)
  "DEV-003": { left: "775px", top: "105px", icon: "⛽" },  // C-Block Wing (Top-right header)
  "DEV-004": { left: "275px", top: "365px", icon: "🔐" },  // SVP Admin Block (Top-right header)
  "DEV-005": { left: "505px", top: "365px", icon: "🖨️" },  // Xerox Shop (Top-right header)
  "DEV-006": { left: "715px", top: "365px", icon: "☕" },  // Nescafe Outlet (Top-right header)
  "DEV-007": { left: "840px", top: "105px", icon: "🌡️" },  // Central Library Temp Sensor
  "DEV-008": { left: "910px", top: "105px", icon: "🚨" },  // Central Library Fire Alarm
  "DEV-009": { left: "915px", top: "365px", icon: "📡" },  // Main Security Gate
};

export function BuildingMap({ devices }: { devices: MockDevice[] }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <section className="map-panel panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">NHCE CAMPUS TELEMETRY · ARCHITECTURAL MAP</span>
          <h2>NHCE College Operational Campus Map</h2>
        </div>
        <div className="floor-tabs">
          <span className="active">EXECUTIVE MAP</span>
          <span>BUILDING BLOCKS</span>
          <span>TELEMETRY BUS</span>
        </div>
      </div>

      <div className="blueprint-map-container">
        {/* Executive Clean SVG Architectural Map */}
        <svg viewBox="0 0 1000 540" className="nhce-blueprint-svg" role="img" aria-label="NHCE Campus Operational Blueprint Map">
          {/* Base Layer Background */}
          <rect width="1000" height="540" rx="8" fill="var(--color-surface-raised)" />
          
          {/* Subtle Outer Campus Boundary */}
          <rect x="24" y="20" width="952" height="500" rx="10" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" strokeDasharray="6 6" />
          <text x="40" y="40" fill="var(--color-text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.14em" opacity="0.75">
            NEW HORIZON COLLEGE OF ENGINEERING · MAIN CAMPUS
          </text>

          {/* North Academic Quad Zone */}
          <rect x="40" y="54" width="920" height="205" rx="8" fill="color-mix(in srgb, var(--cyan) 3%, transparent)" stroke="var(--cyan)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.4" />
          <text x="52" y="70" fill="var(--cyan)" fontSize="9" fontWeight="700" letterSpacing="0.1em">NORTH ACADEMIC QUAD</text>

          {/* South Amenities & Services Zone */}
          <rect x="40" y="315" width="920" height="195" rx="8" fill="color-mix(in srgb, var(--amber) 3%, transparent)" stroke="var(--amber)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.4" />
          <text x="52" y="331" fill="var(--amber)" fontSize="9" fontWeight="700" letterSpacing="0.1em">SOUTH AMENITIES &amp; SERVICES ZONE</text>

          {/* Main Campus Boulevard */}
          <g>
            <rect x="24" y="272" width="952" height="30" fill="color-mix(in srgb, var(--color-text) 4%, transparent)" />
            <line x1="24" y1="287" x2="976" y2="287" stroke="var(--amber)" strokeWidth="1.2" strokeDasharray="12 8" opacity="0.7" />
            <text x="500" y="267" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8" fontWeight="700" letterSpacing="0.18em">MAIN CAMPUS BOULEVARD</text>
          </g>

          {/* Clean Telemetry Bus Conduits (Routing smoothly between cards) */}
          <g opacity="0.75">
            <path d="M 150 240 V 287 H 440 V 240" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 700 240 V 287 H 880 V 240" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 180 350 V 287 H 430 V 350" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 650 350 V 287 H 880 V 350" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
          </g>

          {/* ------------------- CLEAN BUILDING CARDS ------------------- */}

          {/* 1. A-BLOCK (CSE & IT - PI-001) */}
          <g className="building-group">
            <rect x="52" y="85" width="190" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="64" y="97" width="60" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="94" y="111" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">A-BLOCK</text>
            <text x="64" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">CSE &amp; IT Wing</text>
            <text x="64" y="165" fill="var(--color-text-muted)" fontSize="10">Computer Science Dept</text>
            <text x="64" y="185" fill="var(--cyan)" fontSize="9" fontWeight="700">Raspberry Pi · CCTV Camera</text>
          </g>

          {/* 2. B-BLOCK (ENGINEERING - DEV-002) */}
          <g className="building-group">
            <rect x="340" y="85" width="205" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="352" y="97" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="407" y="111" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">INDUSTRIAL BAY</text>
            <text x="352" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">B-Block Engineering</text>
            <text x="352" y="165" fill="var(--color-text-muted)" fontSize="10">Mech &amp; Civil Departments</text>
            <text x="352" y="185" fill="var(--amber)" fontSize="9" fontWeight="700">Industrial Water Pump</text>
          </g>

          {/* 3. C-BLOCK (EEE & ECE - DEV-003) */}
          <g className="building-group">
            <rect x="600" y="85" width="205" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="612" y="97" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="667" y="111" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">ELECTRONICS LABS</text>
            <text x="612" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">C-Block Wing</text>
            <text x="612" y="165" fill="var(--color-text-muted)" fontSize="10">EEE &amp; ECE Research Labs</text>
            <text x="612" y="185" fill="var(--cyan)" fontSize="9" fontWeight="700">Motor Gas Sensor</text>
          </g>

          {/* 4. CENTRAL LIBRARY (EXPANDED FOR DEV-007 & DEV-008) */}
          <g className="building-group">
            <rect x="825" y="85" width="125" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="835" y="97" width="50" height="18" rx="3" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="860" y="110" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">HUB</text>
            <text x="835" y="145" fill="var(--color-text)" fontSize="12" fontWeight="800">Central Library</text>
            <text x="835" y="165" fill="var(--color-text-muted)" fontSize="9.5">Main Knowledge Hub</text>
            <text x="835" y="185" fill="var(--cyan)" fontSize="8.5" fontWeight="700">Temp &amp; Fire Alarm</text>
          </g>

          {/* 5. SVP ADMINISTRATIVE BLOCK (DEV-004) */}
          <g className="building-group">
            <rect x="52" y="345" width="250" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="64" y="357" width="100" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="114" y="371" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">MAIN ENTRANCE</text>
            <text x="64" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">SVP Administrative Block</text>
            <text x="64" y="425" fill="var(--color-text-muted)" fontSize="10">Sardar Vallabhbhai Patel Wing</text>
            <text x="64" y="445" fill="var(--cyan)" fontSize="9" fontWeight="700">IoT Smart Door Lock</text>
          </g>

          {/* 6. XEROX SHOP (DEV-005) */}
          <g className="building-group">
            <rect x="340" y="345" width="190" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="352" y="357" width="90" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="397" y="371" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">SERVICES HUB</text>
            <text x="352" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">Xerox Shop</text>
            <text x="352" y="425" fill="var(--color-text-muted)" fontSize="10">Student Reprographics</text>
            <text x="352" y="445" fill="var(--amber)" fontSize="9" fontWeight="700">Enterprise IoT Printer</text>
          </g>

          {/* 7. NESCAFE OUTLET (DEV-006) */}
          <g className="building-group">
            <rect x="560" y="345" width="180" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="572" y="357" width="80" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="612" y="371" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">FOOD COURT</text>
            <text x="572" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">Nescafe Outlet</text>
            <text x="572" y="425" fill="var(--color-text-muted)" fontSize="10">Campus Food Court</text>
            <text x="572" y="445" fill="var(--amber)" fontSize="9" fontWeight="700">IoT Smoke Detector</text>
          </g>

          {/* 8. MAIN SECURITY GATE (DEV-009) */}
          <g className="building-group">
            <rect x="825" y="345" width="125" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="835" y="357" width="60" height="18" rx="3" fill="color-mix(in srgb, var(--cyan) 10%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="865" y="369" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">GATE</text>
            <text x="835" y="405" textAnchor="middle" fill="var(--color-text)" fontSize="12" fontWeight="800">Main Gate</text>
            <text x="835" y="425" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9.5">Security Post</text>
            <text x="835" y="445" textAnchor="middle" fill="var(--cyan)" fontSize="8.5" fontWeight="700">Weather Sensor</text>
          </g>

          {/* Compass Rose */}
          <g transform="translate(930, 495)">
            <circle cx="0" cy="0" r="12" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" />
            <path d="M 0 -8 L 2.5 0 L 0 2.5 L -2.5 0 Z" fill="var(--cyan)" />
            <text x="0" y="-11" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">N</text>
          </g>
        </svg>

        {/* ------------------- CLEAN INTERACTIVE PINS ------------------- */}
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

              {/* Clean Blueprint Tooltip */}
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


