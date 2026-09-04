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
import { apiJson } from "@/lib/aegisApi";

export function FleetDashboard() {
  const { devices, connected, error } = useDevices();
  const { theme, toggleTheme } = useTheme();
  const [openModule, setOpenModule] = useState<"xai" | "poc" | "research" | null>(null);
  const [reportEmail, setReportEmail] = useState("");
  const [emailSaved, setEmailSaved] = useState(false);
  const [emailSaveError, setEmailSaveError] = useState(false);
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpenModule(null); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);
  useEffect(() => {
    document.body.style.overflow = openModule ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [openModule]);
  useEffect(() => {
    void apiJson<{ recipient?: string }>("/api/v1/notifications/recipient").then((result) => setReportEmail(result.recipient ?? "")).catch(() => undefined);
  }, []);
  const saveReportEmail = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await apiJson("/api/v1/notifications/recipient", { method: "POST", body: JSON.stringify({ email: reportEmail }) });
      setEmailSaved(true);
      setEmailSaveError(false);
      window.setTimeout(() => setEmailSaved(false), 2200);
    } catch {
      setEmailSaved(false);
      setEmailSaveError(true);
    }
  };
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
        <details className="notification-preferences"><summary title="Forensic report email">REPORT EMAIL</summary><form onSubmit={saveReportEmail}><label htmlFor="forensic-report-email">Forensic reports</label><input id="forensic-report-email" type="email" value={reportEmail} onChange={(event) => { setReportEmail(event.target.value); setEmailSaveError(false); }} placeholder="you@example.com" required /><button type="submit">{emailSaved ? "SAVED" : "SET"}</button>{emailSaveError && <small>BACKEND UNAVAILABLE</small>}</form></details>
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

