export type DeviceType = "Camera" | "Temperature Sensor" | "Motion Sensor" | "Fire Alarm" | "Smart Lock" | "Door Sensor" | "Air Quality Sensor" | "Light Sensor" | "Smoke Detector" | "Pressure Sensor";
export type DeviceStatus = "healthy" | "warning" | "compromised" | "critical";
export type TrafficMetrics = { packetSize: number; interArrivalTime: number; entropy: number; symmetry: number };
export type MockDevice = { id: string; name: string; type: DeviceType; location: string; floor: number; room: string; baseline: TrafficMetrics; current: TrafficMetrics; thresholds: TrafficMetrics; trustScore: number; status: DeviceStatus; source?: "mock" | "pi"; sourceMode?: string; sensor?: string; attackType?: string; confidence?: number; activeIncidentId?: string | null; backendState?: import("./aegisApi").AegisDeviceState };

const device = (id: string, name: string, type: DeviceType, location: string, floor: number, metrics: TrafficMetrics, thresholds: TrafficMetrics): MockDevice => ({ id, name, type, location, floor, room: location, baseline: metrics, current: { ...metrics }, thresholds, trustScore: 100, status: "healthy" });

export const mockDevices: MockDevice[] = [
  device("CAM-001", "Perimeter Camera", "Camera", "Security Room", 1, { packetSize: 860, interArrivalTime: 42, entropy: .74, symmetry: .91 }, { packetSize: .25, interArrivalTime: .25, entropy: .2, symmetry: .2 }),
  device("CAM-002", "Reception Camera", "Camera", "Reception", 1, { packetSize: 780, interArrivalTime: 50, entropy: .68, symmetry: .88 }, { packetSize: .25, interArrivalTime: .25, entropy: .2, symmetry: .2 }),
  device("TMP-001", "Server Temperature", "Temperature Sensor", "Server Room", 1, { packetSize: 96, interArrivalTime: 1200, entropy: .31, symmetry: .98 }, { packetSize: .2, interArrivalTime: .3, entropy: .25, symmetry: .15 }),
  device("MOT-001", "Hallway Motion", "Motion Sensor", "Hallway", 1, { packetSize: 128, interArrivalTime: 640, entropy: .42, symmetry: .84 }, { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .25 }),
  device("FIRE-001", "Office Fire Alarm", "Fire Alarm", "Office Floor", 2, { packetSize: 144, interArrivalTime: 900, entropy: .22, symmetry: .99 }, { packetSize: .2, interArrivalTime: .25, entropy: .3, symmetry: .12 }),
  device("LOCK-001", "Main Entrance Lock", "Smart Lock", "Main Entrance", 1, { packetSize: 310, interArrivalTime: 180, entropy: .63, symmetry: .72 }, { packetSize: .3, interArrivalTime: .35, entropy: .25, symmetry: .3 }),
  device("AIR-001", "Lab Air Quality", "Air Quality Sensor", "Laboratory", 2, { packetSize: 260, interArrivalTime: 420, entropy: .57, symmetry: .81 }, { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .25 }),
  device("LIGHT-001", "Conference Light", "Light Sensor", "Conference Room", 2, { packetSize: 112, interArrivalTime: 760, entropy: .36, symmetry: .94 }, { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .2 }),
  device("SMOKE-001", "Storage Smoke Detector", "Smoke Detector", "Storage Room", 1, { packetSize: 152, interArrivalTime: 1040, entropy: .25, symmetry: .97 }, { packetSize: .2, interArrivalTime: .25, entropy: .3, symmetry: .15 }),
  device("PRESS-001", "Electrical Pressure", "Pressure Sensor", "Electrical Room", 1, { packetSize: 184, interArrivalTime: 530, entropy: .48, symmetry: .89 }, { packetSize: .25, interArrivalTime: .3, entropy: .25, symmetry: .25 })
];
