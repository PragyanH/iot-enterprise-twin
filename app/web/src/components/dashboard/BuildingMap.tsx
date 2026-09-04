"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";

// Helper mapping for device status colors and icons
const deviceMeta: Record<string, { icon: string }> = {
  "PI-001": { icon: "📹" },
  "DEV-002": { icon: "💧" },
  "DEV-003": { icon: "⛽" },
  "DEV-004": { icon: "🔐" },
  "DEV-005": { icon: "🖨️" },
  "DEV-006": { icon: "☕" },
  "DEV-007": { icon: "🌡️" },
  "DEV-008": { icon: "🚨" },
  "DEV-009": { icon: "📡" },
};

function DevicePinBadge({
  device,
  cx,
  cy,
  onHover,
  onLeave,
}: {
  device?: MockDevice;
  cx: number;
  cy: number;
  onHover: () => void;
  onLeave: () => void;
}) {
  if (!device) return null;
  const meta = deviceMeta[device.id] ?? { icon: "📍" };
  const href = device.id === "PI-001" ? "/dashboard/hardware/pi-001" : `/dashboard/device/${device.id}`;

  const statusColor =
    device.status === "critical"
      ? "var(--red)"
      : device.status === "warning"
      ? "var(--amber)"
      : "var(--green)";

  return (
    <g
      transform={`translate(${cx}, ${cy})`}
      style={{ cursor: "pointer" }}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      <Link href={href}>
        {/* Outer Glow Halo */}
        <circle cx="0" cy="0" r="14" fill={statusColor} opacity="0.18" />
        
        {/* Head Badge Circle */}
        <circle cx="0" cy="0" r="11" fill="var(--color-surface)" stroke={statusColor} strokeWidth="1.8" />
        <text x="0" y="4" textAnchor="middle" fontSize="10">{meta.icon}</text>

        {/* Tag Pill */}
        <rect x="-24" y="14" width="48" height="15" rx="3" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" />
        <text x="0" y="25" textAnchor="middle" fill="var(--color-text)" fontSize="8.5" fontWeight="800" letterSpacing="0.04em">
          {device.id}
        </text>

        {/* Status Dot */}
        <circle cx="18" cy="14" r="3" fill={statusColor} />
      </Link>
    </g>
  );
}

export function BuildingMap({ devices }: { devices: MockDevice[] }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const deviceMap = new Map(devices.map((d) => [d.id, d]));

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

      <div className="blueprint-map-container" style={{ position: "relative" }}>
        {/* Fully Responsive & Locked Architectural SVG */}
        <svg viewBox="0 0 1000 540" className="nhce-blueprint-svg" role="img" aria-label="NHCE Campus Operational Blueprint Map">
          {/* Base Layer Background */}
          <rect width="1000" height="540" rx="8" fill="var(--color-surface-raised)" />
          
          {/* Outer Campus Boundary */}
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

          {/* Telemetry Bus Conduits */}
          <g opacity="0.6">
            <path d="M 150 240 V 287 H 440 V 240" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 700 240 V 287 H 880 V 240" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 180 350 V 287 H 430 V 350" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
            <path d="M 650 350 V 287 H 880 V 350" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeDasharray="6 4" />
          </g>

          {/* ------------------- BUILDING CARDS WITH EMBEDDED PINS ------------------- */}

          {/* 1. A-BLOCK (PI-001) */}
          <g className="building-group">
            <rect x="52" y="85" width="200" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="64" y="97" width="60" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="94" y="111" textAnchor="middle" fill="var(--cyan)" fontSize="9" fontWeight="800">A-BLOCK</text>
            <text x="64" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">CSE &amp; IT Wing</text>
            <text x="64" y="165" fill="var(--color-text-muted)" fontSize="10">Computer Science Dept</text>
            <text x="64" y="185" fill="var(--cyan)" fontSize="9" fontWeight="700">Raspberry Pi · CCTV Camera</text>
            {/* Embedded Pin PI-001 */}
            <DevicePinBadge
              device={deviceMap.get("PI-001")}
              cx={215}
              cy={110}
              onHover={() => setHoveredId("PI-001")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 2. B-BLOCK (DEV-002) */}
          <g className="building-group">
            <rect x="292" y="85" width="210" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="304" y="97" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="359" y="111" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">INDUSTRIAL BAY</text>
            <text x="304" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">B-Block Engineering</text>
            <text x="304" y="165" fill="var(--color-text-muted)" fontSize="10">Mech &amp; Civil Departments</text>
            <text x="304" y="185" fill="var(--amber)" fontSize="9" fontWeight="700">Industrial Water Pump</text>
            {/* Embedded Pin DEV-002 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-002")}
              cx={465}
              cy={110}
              onHover={() => setHoveredId("DEV-002")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 3. C-BLOCK (DEV-003) */}
          <g className="building-group">
            <rect x="542" y="85" width="210" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="554" y="97" width="110" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="609" y="111" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">ELECTRONICS LABS</text>
            <text x="554" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">C-Block Wing</text>
            <text x="554" y="165" fill="var(--color-text-muted)" fontSize="10">EEE &amp; ECE Research Labs</text>
            <text x="554" y="185" fill="var(--cyan)" fontSize="9" fontWeight="700">Motor Gas Sensor</text>
            {/* Embedded Pin DEV-003 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-003")}
              cx={715}
              cy={110}
              onHover={() => setHoveredId("DEV-003")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 4. CENTRAL LIBRARY (DEV-007 & DEV-008 SIDE BY SIDE) */}
          <g className="building-group">
            <rect x="792" y="85" width="158" height="155" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="802" y="97" width="44" height="18" rx="3" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="824" y="110" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">HUB</text>
            <text x="802" y="145" fill="var(--color-text)" fontSize="13" fontWeight="800">Central Library</text>
            <text x="802" y="165" fill="var(--color-text-muted)" fontSize="10">Main Knowledge Hub</text>
            <text x="802" y="185" fill="var(--cyan)" fontSize="9" fontWeight="700">Temp &amp; Fire Alarm</text>
            {/* Embedded Pin DEV-007 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-007")}
              cx={865}
              cy={110}
              onHover={() => setHoveredId("DEV-007")}
              onLeave={() => setHoveredId(null)}
            />
            {/* Embedded Pin DEV-008 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-008")}
              cx={918}
              cy={110}
              onHover={() => setHoveredId("DEV-008")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 5. SVP ADMINISTRATIVE BLOCK (DEV-004) */}
          <g className="building-group">
            <rect x="52" y="345" width="220" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="64" y="357" width="95" height="20" rx="4" fill="color-mix(in srgb, var(--cyan) 12%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="111" y="371" textAnchor="middle" fill="var(--cyan)" fontSize="8" fontWeight="800">MAIN ENTRANCE</text>
            <text x="64" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">SVP Admin Block</text>
            <text x="64" y="425" fill="var(--color-text-muted)" fontSize="10">Sardar Vallabhbhai Patel Wing</text>
            <text x="64" y="445" fill="var(--cyan)" fontSize="9" fontWeight="700">IoT Smart Door Lock</text>
            {/* Embedded Pin DEV-004 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-004")}
              cx={235}
              cy={370}
              onHover={() => setHoveredId("DEV-004")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 6. XEROX SHOP (DEV-005) */}
          <g className="building-group">
            <rect x="302" y="345" width="200" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="314" y="357" width="90" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="359" y="371" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">SERVICES HUB</text>
            <text x="314" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">Xerox Shop</text>
            <text x="314" y="425" fill="var(--color-text-muted)" fontSize="10">Student Reprographics</text>
            <text x="314" y="445" fill="var(--amber)" fontSize="9" fontWeight="700">Enterprise IoT Printer</text>
            {/* Embedded Pin DEV-005 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-005")}
              cx={465}
              cy={370}
              onHover={() => setHoveredId("DEV-005")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 7. NESCAFE OUTLET (DEV-006) */}
          <g className="building-group">
            <rect x="532" y="345" width="200" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="544" y="357" width="80" height="20" rx="4" fill="color-mix(in srgb, var(--amber) 12%, transparent)" stroke="var(--amber)" strokeWidth="1" />
            <text x="584" y="371" textAnchor="middle" fill="var(--amber)" fontSize="8" fontWeight="800">FOOD COURT</text>
            <text x="544" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">Nescafe Outlet</text>
            <text x="544" y="425" fill="var(--color-text-muted)" fontSize="10">Campus Food Court</text>
            <text x="544" y="445" fill="var(--amber)" fontSize="9" fontWeight="700">IoT Smoke Detector</text>
            {/* Embedded Pin DEV-006 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-006")}
              cx={695}
              cy={370}
              onHover={() => setHoveredId("DEV-006")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* 8. MAIN SECURITY GATE (DEV-009) */}
          <g className="building-group">
            <rect x="762" y="345" width="188" height="150" rx="8" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1.5" />
            <rect x="774" y="357" width="55" height="18" rx="3" fill="color-mix(in srgb, var(--cyan) 10%, transparent)" stroke="var(--cyan)" strokeWidth="1" />
            <text x="801" y="369" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">GATE</text>
            <text x="774" y="405" fill="var(--color-text)" fontSize="13" fontWeight="800">Main Gate</text>
            <text x="774" y="425" fill="var(--color-text-muted)" fontSize="10">Security Post</text>
            <text x="774" y="445" fill="var(--cyan)" fontSize="9" fontWeight="700">Weather Sensor</text>
            {/* Embedded Pin DEV-009 */}
            <DevicePinBadge
              device={deviceMap.get("DEV-009")}
              cx={915}
              cy={370}
              onHover={() => setHoveredId("DEV-009")}
              onLeave={() => setHoveredId(null)}
            />
          </g>

          {/* Compass Rose */}
          <g transform="translate(930, 495)">
            <circle cx="0" cy="0" r="12" fill="var(--color-surface)" stroke="var(--color-border-strong)" strokeWidth="1" />
            <path d="M 0 -8 L 2.5 0 L 0 2.5 L -2.5 0 Z" fill="var(--cyan)" />
            <text x="0" y="-11" textAnchor="middle" fill="var(--cyan)" fontSize="7.5" fontWeight="800">N</text>
          </g>
        </svg>

        {/* SVG Interactive Hover Tooltip Overlay */}
        {hoveredId && deviceMap.has(hoveredId) && (() => {
          const dev = deviceMap.get(hoveredId)!;
          const statusColor = dev.status === "critical" ? "var(--red)" : dev.status === "warning" ? "var(--amber)" : "var(--green)";
          return (
            <div
              className="blueprint-tooltip"
              style={{
                position: "absolute",
                top: "14px",
                right: "14px",
                opacity: 1,
                pointerEvents: "none",
                borderColor: statusColor,
              }}
            >
              <div className="tooltip-header">
                <span className="tooltip-id">{dev.id}</span>
                <span className={`tooltip-badge badge-${dev.status}`}>{dev.status.toUpperCase()}</span>
              </div>
              <strong>{dev.name}</strong>
              <small className="tooltip-location">📍 {dev.location}</small>
              <div className="tooltip-meta">
                <span>Trust: <b>{dev.trustScore}/100</b></span>
                <span>Sensor: <b>{dev.type}</b></span>
              </div>
              <span className="tooltip-cta">CLICK TO INSPECT TELEMETRY →</span>
            </div>
          );
        })()}

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


