"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useDevices } from "@/features/device/DeviceProvider";
import { useTheme } from "@/context/ThemeContext";
import { BuildingMap } from "./BuildingMap";
import { DeviceList } from "./DeviceList";
import { FleetStats } from "./FleetStats";
import { AttackLifecycleDemo } from "@/components/aegis/AttackLifecycleDemo";
import { CompetitiveLandscape } from "@/components/aegis/CompetitiveLandscape";
import { IndustrialHardware } from "@/components/aegis/IndustrialHardware";
import { EnterpriseArchitectureMap } from "@/components/aegis/EnterpriseArchitectureMap";
import { ResearchPaperModal } from "@/components/aegis/ResearchPaperModal";

export function FleetDashboard() {
  const { devices, connected, error } = useDevices();
  const { theme, toggleTheme } = useTheme();
  const [openModule, setOpenModule] = useState<"xai" | "poc" | "research" | null>(null);
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpenModule(null); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);
  useEffect(() => {
    document.body.style.overflow = openModule ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [openModule]);
  return <main className="soc-page">
    <header className="topbar">
      <Link href="/dashboard" className="brand"><span className="brand-mark">A</span><span>AEGIS<span>-TWIN</span></span></Link>
      <nav>
        <Link className="nav-active" href="/dashboard">Fleet overview</Link>
        <button
          type="button"
          onClick={() => setOpenModule("research")}
          style={{ background: "transparent", border: 0, color: "var(--muted)", cursor: "pointer", fontSize: "11px", fontWeight: "600", padding: "0 8px" }}
        >
          Research
        </button>
        <Link href="/reports">Reports</Link>
      </nav>
      <div className="topbar-right">
        <button type="button" className="theme-toggle-btn" onClick={toggleTheme} aria-label="Toggle theme">
          <span className="theme-toggle-icon">{theme === "dark" ? "☀️ Light" : "🌙 Dark"}</span>
        </button>
        <span className="operator"><i /> SOC / OPERATOR 07</span>
      </div>
    </header>
    <div className="page-wrap">
      <div className="page-intro"><div><span className="eyebrow">Security operations center · live hybrid telemetry</span><h1>IoT Security Overview</h1><p>Telemetry posture across the Aegis-Twin enterprise facility.</p></div><div className="system-state" title={error ?? undefined}><i /> {connected ? "SYSTEM NOMINAL" : "BACKEND RECONNECTING"}<small>{connected ? "SSE live" : "Using last known state"}</small></div></div>
      <FleetStats devices={devices} />
      <div className="fleet-layout"><BuildingMap devices={devices} /><DeviceList devices={devices} /></div>
      <IndustrialHardware />
      <div className="module-launch-row"><button className="module-launch-button" onClick={() => setOpenModule("xai")}>EXPLAINABLE AI LAB <span>OPEN FULL VIEW →</span></button><button className="module-launch-button" onClick={() => setOpenModule("poc")}>POC MODULE <span>OPEN FULL VIEW →</span></button></div>
      <EnterpriseArchitectureMap />
    </div>
    {openModule && (
      openModule === "research" ? (
        <ResearchPaperModal onClose={() => setOpenModule(null)} />
      ) : (
        <div className="module-modal" role="dialog" aria-modal="true" aria-label={openModule === "xai" ? "XAI full view" : "POC full view"} onMouseDown={(event) => { if (event.target === event.currentTarget) setOpenModule(null); }}><div className="module-modal-content"><button className="module-modal-close" onClick={() => setOpenModule(null)} aria-label="Close full view">×</button>{openModule === "xai" ? <AttackLifecycleDemo /> : <CompetitiveLandscape />}</div></div>
      )
    )}
  </main>;
}

