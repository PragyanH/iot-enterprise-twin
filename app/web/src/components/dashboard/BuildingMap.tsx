"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";

// Dedicated badge positions at top-right corner of each building card to prevent any text collision
const devicePinCoords: Record<string, { left: string; top: string; icon: string }> = {
  "PI-001": { left: "22%", top: "18%", icon: "📹" },  // A-Block CCTV (Raspberry Pi)
  "DEV-002": { left: "52%", top: "18%", icon: "💧" },  // B-Block Industrial Water Pump
  "DEV-003": { left: "77%", top: "18%", icon: "⛽" },  // C-Block Motor Gas Sensor
  "DEV-004": { left: "28%", top: "64%", icon: "🔐" },  // SVP Block Smart Door Lock
  "DEV-005": { left: "50%", top: "64%", icon: "🖨️" },  // Xerox Shop IoT Printer
  "DEV-006": { left: "71%", top: "64%", icon: "☕" },  // Nescafe Outlet Smoke Detector
  "DEV-007": { left: "91%", top: "16%", icon: "🌡️" },  // Central Library Temp Sensor
  "DEV-008": { left: "91%", top: "34%", icon: "🚨" },  // Central Library Smart Fire Alarm
  "DEV-009": { left: "91%", top: "64%", icon: "📡" },  // Main Security Gate Weather Sensor
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
        <svg viewBox="0 0 1000 560" className="nhce-blueprint-svg" role="img" aria-label="NHCE Campus Operational Blueprint Map">
          {/* Base Layer Background */}
          <rect width="1000" height="560" rx="8" fill="var(--color-surface-raised)" />
          
          {/* Subtle Outer Campus Boundary */}
          <rect x="30" y="24" width="940" height="512" rx="10" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" strokeDasharray="6 6" />
          <text x="44" y="44" fill="var(--color-text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.14em" opacity="0.75">
            NEW HORIZON COLLEGE OF ENGINEERING · MAIN CAMPUS
          </text>

          {/* North Academic Quad Zone */}
          <rect x="50" y="58" width="890" height="210" rx="8" fill="color-mix(in srgb, var(--cyan) 3%, transparent)" stroke="var(--cyan)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.4" />
          <text x="62" y="74" fill="var(--cyan)" fontSize="9" fontWeight="700" letterSpacing="0.1em">NORTH ACADEMIC QUAD</text>

          {/* South Amenities & Services Zone */}
          <rect x="50" y="310" width="890" height="210" rx="8" fill="color-mix(in srgb, var(--amber) 3%, transparent)" stroke="var(--amber)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.4" />
          <text x="62" y="326" fill="var(--amber)" fontSize="9" fontWeight="700" letterSpacing="0.1em">SOUTH AMENITIES &amp; SERVICES ZONE</text>

          {/* Main Campus Boulevard (Clean Road Rendering) */}
          <g>
            <rect x="30" y="274" width="940" height="30" fill="color-mix(in srgb, var(--color-text) 4%, transparent)" />
            <line x1="30" y1="289" x2="970" y2="289" stroke="var(--amber)" strokeWidth="1.2" strokeDasharray="12 8" opacity="0.7" />
            <text x="500" y="270" textAnchor="middle" fill="var(--color-text-muted)" fontSize="8" fontWeight="700" letterSpacing="0.18em">MAIN CAMPUS BOULEVARD</text>
          </g>

          {/* Subtle Telemetry Bus Conduits (Clean 1.5px lines without harsh neon glow) */}
          <g opacity="0.85">
            <path d="M 140 160 H 440 H 690 V 289 H 880 V 130" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 180 430 H 430 H 650 V 289 H 880 V 430" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
          </g>

          {/* ------------------- CLEAN BUILDING CARDS ------------------- */}

          {/* 1. A-BLOCK (CSE & IT - PI-001) */}
          <g className="building-group">
            <rect x="60" y="90" width="180" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="72" y="102" width="60" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="102" y="116" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">A-BLOCK</text>
            <text x="72" y="148" fill="var(--color-text)" fontSize="13" fontWeight="800">CSE &amp; IT Wing</text>
            <text x="72" y="168" fill="var(--color-text-muted)" fontSize="10">Computer Science Dept</text>
            <text x="72" y="186" fill="var(--cyan)" fontSize="9" fontWeight="700">Raspberry Pi · CCTV Camera</text>
          </g>

          {/* 2. B-BLOCK (ENGINEERING - DEV-002) */}
          <g className="building-group">
            <rect x="340" y="90" width="200" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="352" y="102" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="407" y="116" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">INDUSTRIAL BAY</text>
            <text x="352" y="148" fill="var(--color-text)" fontSize="13" fontWeight="800">B-Block Engineering</text>
            <text x="352" y="168" fill="var(--color-text-muted)" fontSize="10">Mech &amp; Civil Departments</text>
            <text x="352" y="186" fill="var(--amber)" fontSize="9" fontWeight="700">Industrial Water Pump</text>
          </g>

          {/* 3. C-BLOCK (EEE & ECE - DEV-003) */}
          <g className="building-group">
            <rect x="590" y="90" width="200" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="602" y="102" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="657" y="116" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">ELECTRONICS LABS</text>
            <text x="602" y="148" fill="var(--color-text)" fontSize="13" fontWeight="800">C-Block Wing</text>
            <text x="602" y="168" fill="var(--color-text-muted)" fontSize="10">EEE &amp; ECE Research Labs</text>
            <text x="602" y="186" fill="var(--cyan)" fontSize="9" fontWeight="700">Motor Gas Sensor</text>
          </g>

          {/* 4. CENTRAL LIBRARY (DEV-007 & DEV-008) */}
          <g className="building-group">
            <rect x="830" y="80" width="100" height="170" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <circle cx="880" cy="120" r="22" fill="color-mix(in srgb, var(--cyan) 8%, transparent)" stroke="var(--cyan)" strokeWidth="1" strokeDasharray="3 3" />
            <text x="880" y="174" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">Central Library</text>
            <text x="880" y="192" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Main Knowledge Hub</text>
            <text x="880" y="210" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="700">Temp &amp; Fire Alarm</text>
          </g>

          {/* 5. SVP ADMINISTRATIVE BLOCK (DEV-004) */}
          <g className="building-group">
            <rect x="60" y="350" width="240" height="140" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="72" y="362" width="100" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="122" y="376" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">MAIN ENTRANCE</text>
            <text x="72" y="408" fill="var(--color-text)" fontSize="13" fontWeight="800">SVP Administrative Block</text>
            <text x="72" y="428" fill="var(--color-text-muted)" fontSize="10">Sardar Vallabhbhai Patel Wing</text>
            <text x="72" y="446" fill="var(--cyan)" fontSize="9" fontWeight="700">IoT Smart Door Lock</text>
          </g>

          {/* 6. XEROX SHOP (DEV-005) */}
          <g className="building-group">
            <rect x="340" y="350" width="180" height="140" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="352" y="362" width="90" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="397" y="376" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">SERVICES HUB</text>
            <text x="352" y="408" fill="var(--color-text)" fontSize="13" fontWeight="800">Xerox Shop</text>
            <text x="352" y="428" fill="var(--color-text-muted)" fontSize="10">Student Reprographics</text>
            <text x="352" y="446" fill="var(--amber)" fontSize="9" fontWeight="700">Enterprise IoT Printer</text>
          </g>

          {/* 7. NESCAFE OUTLET (DEV-006) */}
          <g className="building-group">
            <rect x="560" y="350" width="170" height="140" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <circle cx="680" cy="372" r="12" fill="color-mix(in srgb, var(--amber) 14%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="680" y="376" textAnchor="middle" fill="var(--amber)" fontSize="10">☕</text>
            <text x="572" y="408" fill="var(--color-text)" fontSize="13" fontWeight="800">Nescafe Outlet</text>
            <text x="572" y="428" fill="var(--color-text-muted)" fontSize="10">Campus Food Court</text>
            <text x="572" y="446" fill="var(--amber)" fontSize="9" fontWeight="700">IoT Smoke Detector</text>
          </g>

          {/* 8. MAIN SECURITY GATE (DEV-009) */}
          <g className="building-group">
            <rect x="830" y="350" width="100" height="140" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="840" y="360" width="80" height="18" rx="3" fill="color-mix(in srgb, var(--cyan) 10%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="880" y="372" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">CHECKPOINT</text>
            <text x="880" y="410" textAnchor="middle" fill="var(--color-text)" fontSize="11" fontWeight="800">Main Gate</text>
            <text x="880" y="428" textAnchor="middle" fill="var(--color-text-muted)" fontSize="9">Security Post</text>
            <text x="880" y="446" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="700">Weather Sensor</text>
          </g>

          {/* Minimal Compass Rose */}
          <g transform="translate(940, 520)">
            <circle cx="0" cy="0" r="14" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" />
            <path d="M 0 -10 L 3 0 L 0 3 L -3 0 Z" fill="var(--cyan)" />
            <text x="0" y="-13" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">N</text>
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


