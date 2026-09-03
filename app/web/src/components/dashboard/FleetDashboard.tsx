"use client";
import Link from "next/link";
import { useDevices } from "@/features/device/DeviceProvider";
import { BuildingMap } from "./BuildingMap";
import { DeviceList } from "./DeviceList";
import { FleetStats } from "./FleetStats";
export function FleetDashboard() { const { devices } = useDevices(); return <main className="soc-page"><header className="topbar"><Link href="/dashboard" className="brand"><span className="brand-mark">A</span><span>AEGIS<span>-TWIN</span></span></Link><nav><Link className="nav-active" href="/dashboard">Fleet overview</Link><Link href="/reports">Reports</Link></nav><span className="operator"><i /> SOC / OPERATOR 07</span></header><div className="page-wrap"><div className="page-intro"><div><span className="eyebrow">Security operations center · 03 Sep 2026</span><h1>IoT Security Overview</h1><p>Telemetry posture across the Aegis-Twin enterprise facility.</p></div><div className="system-state"><i /> SYSTEM NOMINAL <small>Last sync 14:32:08</small></div></div><FleetStats devices={devices} /><div className="fleet-layout"><BuildingMap devices={devices} /><DeviceList devices={devices} /></div></div></main>; }