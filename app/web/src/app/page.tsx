"use client";

import { useEffect, useMemo, useState } from "react";

type FleetDevice = {
  id: string;
  name: string;
  sector?: string;
  status: string;
  trust: number;
};

const statusClasses: Record<string, string> = {
  Healthy: "bg-brand-success/20 text-brand-success border border-brand-success/30",
  Monitoring: "bg-brand-accent/20 text-brand-accent border border-brand-accent/30",
  Compromised: "bg-brand-danger/20 text-brand-danger border border-brand-danger/30"
};

export default function HomePage() {
  const [fleet, setFleet] = useState<FleetDevice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    let eventSource: EventSource | null = null;

    async function fetchFleet() {
      try {
        const response = await fetch("/api/v1/fleet", {
          signal: controller.signal,
          cache: "no-store"
        });

        if (!response.ok) {
          throw new Error("Failed to load fleet data");
        }

        const data = (await response.json()) as FleetDevice[];
        setFleet(data);

        eventSource = new EventSource("/api/v1/events/trust");
        eventSource.addEventListener("trust", (event) => {
          const payload = JSON.parse((event as MessageEvent<string>).data) as { devices: FleetDevice[] };
          setFleet(payload.devices);
        });
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setFleet([]);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchFleet();
    return () => {
      controller.abort();
      eventSource?.close();
    };
  }, []);

  const totals = useMemo(() => {
    const totalHealthy = fleet.filter((device) => device.status === "Healthy").length;
    const compromised = fleet.filter((device) => device.status === "Compromised").length;
    const avgTrust = fleet.length
      ? Math.round(fleet.reduce((sum, device) => sum + device.trust, 0) / fleet.length)
      : 0;

    return { totalHealthy, compromised, avgTrust };
  }, [fleet]);

  return (
    <main className="min-h-screen px-6 py-8 text-slate-100">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex items-center justify-between gap-4 rounded-2xl border border-slate-700 bg-slate-900/80 p-6 shadow-glow backdrop-blur">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-brand-primary">Aegis-Twin</div>
            <h1 className="mt-2 text-3xl font-semibold text-white">Enterprise Fleet Defense</h1>
          </div>
          <button className="rounded-xl bg-brand-primary px-4 py-2 text-sm font-medium text-slate-950 transition hover:opacity-90">
            Sync telemetry
          </button>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="metric-card rounded-2xl p-5">
            <div className="text-sm text-slate-400">Fleet health</div>
            <div className="mt-3 flex items-baseline justify-between">
              <div className="text-3xl font-bold text-white">{loading ? "--" : `${totals.totalHealthy}/${fleet.length || 0}`}</div>
              <span className="status-dot bg-brand-success" />
            </div>
          </div>
          <div className="metric-card rounded-2xl p-5">
            <div className="text-sm text-slate-400">Average trust</div>
            <div className="mt-3 text-3xl font-bold text-white">{loading ? "--" : `${totals.avgTrust}/100`}</div>
          </div>
          <div className="metric-card rounded-2xl p-5">
            <div className="text-sm text-slate-400">Threats</div>
            <div className="mt-3 flex items-baseline justify-between">
              <div className="text-3xl font-bold text-white">{loading ? "--" : totals.compromised}</div>
              <span className="status-dot bg-brand-danger" />
            </div>
          </div>
        </section>

        <section className="dashboard-shell mt-8 rounded-2xl p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Fleet overview</h2>
            <div className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-300">
              {loading ? "Loading" : "Live view"}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-950/70">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-700 bg-slate-900/80 text-slate-300">
                <tr>
                  <th className="px-4 py-3 font-medium">Device</th>
                  <th className="px-4 py-3 font-medium">Sector</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Trust</th>
                </tr>
              </thead>
              <tbody>
                {fleet.map((device) => (
                  <tr key={device.id} className="border-b border-slate-800 last:border-0 hover:bg-slate-900/60">
                    <td className="px-4 py-3 text-white">{device.id} · {device.name}</td>
                    <td className="px-4 py-3 text-slate-300">{device.sector ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusClasses[device.status] ?? "bg-slate-700 text-slate-200"}`}>
                        {device.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-brand-primary">{device.trust}%</td>
                  </tr>
                ))}
                {!loading && fleet.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                      No fleet data available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
