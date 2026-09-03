"use client";
import Link from "next/link";
import { useState } from "react";
import type { MockDevice } from "@/lib/mockDevices";
import { DeviceStatus } from "./DeviceStatus";
export function DeviceList({ devices }: { devices: MockDevice[] }) {
	const [query, setQuery] = useState("");
	const filteredDevices = devices.filter((device) => `${device.id} ${device.name} ${device.type} ${device.location}`.toLowerCase().includes(query.toLowerCase()));
	return <aside className="device-list panel"><div className="panel-heading"><div><span className="eyebrow">Fleet registry</span><h2>All devices</h2></div><span className="live-chip"><i /> LIVE</span></div><label className="device-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search devices..." aria-label="Search devices" />{query && <button type="button" onClick={() => setQuery("")} aria-label="Clear device search">×</button>}</label><div className="device-list-scroll">{filteredDevices.map((device) => <Link className="device-row" href={`/dashboard/device/${device.id}`} key={device.id}><span className="device-glyph">{device.type === "Camera" ? "◉" : device.type === "Fire Alarm" || device.type === "Smoke Detector" ? "△" : device.type === "Smart Lock" ? "⌑" : "⌁"}</span><span className="device-row-copy"><strong>{device.id}</strong><small>{device.name} · {device.location}</small></span><span className="device-trust">{device.trustScore}<small>%</small><DeviceStatus status={device.status} /></span></Link>)}{filteredDevices.length === 0 && <p className="no-results">No matching devices</p>}</div></aside>;
}