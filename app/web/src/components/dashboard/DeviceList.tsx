"use client";

import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";
import { DeviceStatus } from "./DeviceStatus";

const deviceIcons: Record<string, string> = {
  "PI-001": "📹",
  "DEV-002": "💧",
  "DEV-003": "⛽",
  "DEV-004": "🔐",
  "DEV-005": "🖨️",
  "DEV-006": "☕",
  "DEV-007": "🌡️",
  "DEV-008": "🚨",
  "DEV-009": "📡",
};

export function DeviceList({ devices }: { devices: MockDevice[] }) {
  const [query, setQuery] = useState("");

  const filteredDevices = devices.filter((device) =>
    `${device.id} ${device.name} ${device.type} ${device.location}`.toLowerCase().includes(query.toLowerCase())
  );

  const healthyCount = devices.filter((d) => d.status === "healthy").length;
  const warningCount = devices.filter((d) => d.status === "warning").length;
  const criticalCount = devices.filter((d) => d.status === "critical" || d.status === "compromised").length;

  return (
    <aside className="device-list panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">NHCE FLEET REGISTRY</span>
          <h2>All Active Devices</h2>
        </div>
        <span className="live-chip">
          <i /> LIVE
        </span>
      </div>

      {/* Fleet Summary Counter Bar */}
      <div className="fleet-summary-bar">
        <span className="summary-pill pill-healthy">
          <i /> {healthyCount} Nominal
        </span>
        {warningCount > 0 && (
          <span className="summary-pill pill-warning">
            <i /> {warningCount} Warning
          </span>
        )}
        {criticalCount > 0 && (
          <span className="summary-pill pill-critical">
            <i /> {criticalCount} Critical
          </span>
        )}
      </div>

      {/* Device Search Box */}
      <label className="device-search">
        <span>⌕</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search device by ID, block, or type..."
          aria-label="Search devices"
        />
        {query && (
          <button type="button" onClick={() => setQuery("")} aria-label="Clear search">
            ×
          </button>
        )}
      </label>

      {/* Scrollable Device List Container */}
      <div className="device-list-scroll">
        {filteredDevices.map((device) => {
          const icon = deviceIcons[device.id] ?? "📍";
          const href = device.id === "PI-001" ? "/dashboard/hardware/pi-001" : `/dashboard/device/${device.id}`;

          return (
            <Link className="device-row" href={href} key={device.id}>
              <div className="device-glyph">
                <span>{icon}</span>
              </div>

              <div className="device-row-copy">
                <div className="device-title-line">
                  <strong>{device.id}</strong>
                  <span className="device-location-tag">{device.location}</span>
                </div>
                <small>{device.name}</small>
              </div>

              <div className="device-trust-block">
                <div className="trust-val">
                  <span>{device.trustScore}</span>
                  <small>%</small>
                </div>

                {/* Mini Trust Level Indicator */}
                <div className="mini-trust-bar">
                  <div
                    className={`mini-trust-fill fill-${device.status}`}
                    style={{ width: `${Math.max(5, device.trustScore)}%` }}
                  />
                </div>

                <DeviceStatus status={device.status} />
              </div>
            </Link>
          );
        })}

        {filteredDevices.length === 0 && <p className="no-results">No devices matching &quot;{query}&quot;</p>}
      </div>
    </aside>
  );
}

