export type DeviceType = "Camera" | "Temperature Sensor" | "Motion Sensor" | "Fire Alarm" | "Smart Lock" | "Door Sensor" | "Air Quality Sensor" | "Light Sensor" | "Smoke Detector" | "Pressure Sensor";
export type DeviceStatus = "healthy" | "warning" | "compromised" | "critical";
export type TrafficMetrics = { packetSize: number; interArrivalTime: number; entropy: number; symmetry: number };
export type MockDevice = { id: string; name: string; type: DeviceType; location: string; floor: number; room: string; baseline: TrafficMetrics; current: TrafficMetrics; thresholds: TrafficMetrics; trustScore: number; status: DeviceStatus; source?: "mock" | "pi"; sourceMode?: string; sensor?: string; attackType?: string; confidence?: number; activeIncidentId?: string | null; backendState?: import("./aegisApi").AegisDeviceState };

const device = (id: string, name: string, type: DeviceType, location: string, floor: number, metrics: TrafficMetrics, thresholds: TrafficMetrics): MockDevice => ({ id, name, type, location, floor, room: location, baseline: metrics, current: { ...metrics }, thresholds, trustScore: 100, status: "healthy" });

export const mockDevices: MockDevice[] = [
  device("PI-001", "CCTV Camera", "Camera", "A-Block", 1, { packetSize: 420, interArrivalTime: 120, entropy: .74, symmetry: .92 }, { packetSize: .25, interArrivalTime: .25, entropy: .2, symmetry: .2 }),
  device("DEV-002", "Industrial Water Pump", "Pressure Sensor", "B-Block", 1, { packetSize: 600, interArrivalTime: 300, entropy: .70, symmetry: .50 }, { packetSize: .25, interArrivalTime: .25, entropy: .2, symmetry: .2 }),
  device("DEV-003", "Motor Gas Sensor", "Air Quality Sensor", "C-Block", 1, { packetSize: 350, interArrivalTime: 620, entropy: .45, symmetry: .70 }, { packetSize: .2, interArrivalTime: .3, entropy: .25, symmetry: .15 }),
  device("DEV-004", "Smart Door Lock", "Smart Lock", "Sardar Vallabhbhai Patel Block", 1, { packetSize: 310, interArrivalTime: 180, entropy: .63, symmetry: .72 }, { packetSize: .3, interArrivalTime: .35, entropy: .25, symmetry: .3 }),
  device("DEV-005", "IoT Enterprise Printer", "Door Sensor", "Xerox Shop", 1, { packetSize: 520, interArrivalTime: 420, entropy: .66, symmetry: .56 }, { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .25 }),
  device("DEV-006", "Smart Smoke Detector", "Smoke Detector", "Nescafe Outlet", 1, { packetSize: 152, interArrivalTime: 1040, entropy: .25, symmetry: .97 }, { packetSize: .2, interArrivalTime: .25, entropy: .3, symmetry: .15 }),
  device("DEV-007", "Temperature Sensor", "Temperature Sensor", "Central Library", 1, { packetSize: 96, interArrivalTime: 1200, entropy: .31, symmetry: .98 }, { packetSize: .2, interArrivalTime: .3, entropy: .25, symmetry: .15 }),
  device("DEV-008", "Smart Fire Alarm", "Fire Alarm", "Central Library", 2, { packetSize: 144, interArrivalTime: 900, entropy: .22, symmetry: .99 }, { packetSize: .2, interArrivalTime: .25, entropy: .3, symmetry: .12 }),
  device("DEV-001", "AEGIS Pump 01", "Pressure Sensor", "Alpha", 1, { packetSize: 400, interArrivalTime: 500, entropy: .30, symmetry: .60 }, { packetSize: .25, interArrivalTime: .25, entropy: .2, symmetry: .2 })
];

