"use client";

import Link from "next/link";
import type { MockDevice } from "@/lib/mockDevices";

// Map positions pinpointed accurately to each room center box
const blockPositions: Record<string, { left: string; top: string }> = {
  "PI-001": { left: "20%", top: "31%" },  // A-Block (CCTV) - inside room-a
  "DEV-001": { left: "45%", top: "31%" }, // Alpha (Pump) - inside room-c
  "DEV-002": { left: "70%", top: "31%" }, // Beta (Assembly Arm) - inside room-b
  "DEV-003": { left: "20%", top: "78%" }, // Gamma (Grid Node) - inside room-f
  "DEV-004": { left: "47%", top: "78%" }, // Alpha (Security Camera) - inside room-e
  "DEV-005": { left: "68%", top: "78%" }, // Nescafe Outlet (Smoke Detector) - inside room-g
  "DEV-006": { left: "88%", top: "27%" }, // Central Library (Temp Sensor) - upper right inside room-d
  "DEV-007": { left: "88%", top: "45%" }, // Central Library (Fire Alarm) - lower right inside room-d
  "DEV-008": { left: "88%", top: "78%" }, // Main Security Gate (Environment Sensor) - inside room-h
};

export function BuildingMap({ devices }: { devices: MockDevice[] }) {
  return (
    <section className="map-panel panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">NHCE CAMPUS TELEMETRY · CAMPUS MAP</span>
          <h2>NHCE College Operational Topology Map</h2>
        </div>
        <div className="floor-tabs">
          <span className="active">NHCE CAMPUS</span>
          <span>MAIN BLOCKS</span>
          <span>FACILITIES</span>
        </div>
      </div>
      <div className="floor-plan">
        <div className="floor-label floor-one">ACADEMIC BLOCKS</div>
        <div className="floor-label floor-two">CAMPUS SERVICES & LIBRARY</div>
        
        <div className="room-grid">
          <div className="room room-a">A-BLOCK (CCTV)</div>
          <div className="room room-c">B-BLOCK (PUMP)</div>
          <div className="room room-b">C-BLOCK (GAS)</div>
          <div className="room room-d">CENTRAL LIBRARY</div>
          <div className="room room-f">SVP BLOCK (LOCK)</div>
          <div className="room room-e">XEROX SHOP (PRINTER)</div>
          <div className="room room-g">NESCAFE OUTLET</div>
          <div className="room room-h">SECURITY GATE</div>
          <div className="hallway-line" />
        </div>

        {devices.map((device) => {
          const pos = blockPositions[device.id] ?? { left: "50%", top: "50%" };
          const href = device.id === "PI-001" ? "/dashboard/hardware/pi-001" : `/dashboard/device/${device.id}`;
          
          return (
            <Link
              key={device.id}
              href={href}
              className={`map-marker marker-${device.status}`}
              style={{ left: pos.left, top: pos.top }}
            >
              <span className="map-dot" />
              <b>{device.id}</b>
              <span className="map-tooltip">
                <strong>{device.name}</strong>
                <small>{device.type} · {device.location}</small>
                <em>{device.status.toUpperCase()}</em>
              </span>
            </Link>
          );
        })}

        <div className="map-legend">
          <span><i className="legend-dot healthy" />Healthy</span>
          <span><i className="legend-dot warning" />Warning</span>
          <span><i className="legend-dot critical" />Threat</span>
        </div>
      </div>
    </section>
  );
}
