"use client";

import Link from "next/link";
import { useDevices } from "@/features/device/DeviceProvider";

export function IndustrialHardware() {
  const { devices } = useDevices();
  const pi = devices.find((device) => device.id === "PI-001");

  return (
    <Link href="/dashboard/hardware/pi-001" className="industrial-hardware panel">
      <div className="hardware-copy">
        <span className="eyebrow">A-BLOCK · PI-001 · CCTV CAMERA</span>
        <h2>Raspberry Pi (CCTV)</h2>
        <p>
          Trust {pi?.trustScore ?? "--"}/100 · {(pi?.backendState?.state ?? "BOOTSTRAP").replaceAll("_", " ")} · {pi?.sensor ?? "sensor awaiting telemetry"}. Open A-Block device to inspect live hybrid evidence and remediation.
        </p>
        <span className="hardware-cta">OPEN A-BLOCK PI-001 DASHBOARD →</span>
      </div>

      <div className="hardware-diagram" aria-label="Raspberry Pi security camera connection">
        <svg viewBox="0 0 500 140" role="img">
          {/* Connecting signal line with flow dot */}
          <path className="hardware-line" d="M190 70H310" />
          <circle className="hardware-flow-dot" cx="250" cy="70" r="3.5" />

          {/* Node 1: Raspberry Pi (PI-001) */}
          <g className="hardware-node">
            <rect x="70" y="30" width="120" height="80" rx="6" />
            {/* Chip Body */}
            <rect x="115" y="48" width="30" height="24" rx="2" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" />
            {/* Chip Core Notch */}
            <circle cx="122" cy="54" r="2" fill="var(--color-primary)" />
            {/* Pins (Top & Bottom) */}
            <path d="M120 43v5M127 43v5M134 43v5M141 43v5M120 72v5M127 72v5M134 72v5M141 72v5" stroke="var(--color-primary)" strokeWidth="1.5" />
            {/* Pins (Left & Right) */}
            <path d="M110 54h5M110 60h5M110 66h5M145 54h5M145 60h5M145 66h5" stroke="var(--color-primary)" strokeWidth="1.5" />
            <text x="130" y="94" textAnchor="middle" style={{ fontSize: "9px", fontWeight: 700, fill: "var(--color-text)" }}>RASPBERRY PI</text>
          </g>

          {/* Node 2: Security CCTV Camera */}
          <g className="hardware-node">
            <rect x="310" y="30" width="120" height="80" rx="6" />
            {/* Camera Base Stand */}
            <path d="M362 76h16M370 76v-6" stroke="var(--color-primary)" strokeWidth="1.5" fill="none" />
            {/* CCTV Camera Main Body */}
            <path d="M352 53l24-7a2 2 0 0 1 3 1l3 10a2 2 0 0 1-1 3l-24 7a2 2 0 0 1-3-1l-3-10a2 2 0 0 1 1-3z" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" />
            {/* Camera Lens Circle */}
            <circle cx="355" cy="60" r="4" fill="var(--color-surface-raised)" stroke="var(--color-primary)" strokeWidth="1.5" />
            {/* InfraRed LED Dot */}
            <circle cx="377" cy="51" r="1.5" fill="var(--cyan)" />
            <text x="370" y="94" textAnchor="middle" style={{ fontSize: "9px", fontWeight: 700, fill: "var(--color-text)" }}>SECURITY CAMERA</text>
          </g>

          <text className="hardware-label" x="250" y="58" textAnchor="middle" style={{ fontSize: "8px", fill: "var(--color-text-muted)", letterSpacing: "0.08em" }}>TELEMETRY STREAM</text>
        </svg>
      </div>
    </Link>
  );
}
