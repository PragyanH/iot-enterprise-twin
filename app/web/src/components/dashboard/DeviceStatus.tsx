import type { DeviceStatus } from "@/lib/mockDevices";
import { statusLabel } from "@/lib/securityModel";
export function DeviceStatus({ status }: { status: DeviceStatus }) { return <span className={`status-badge status-${status}`}><span className="status-dot" />{statusLabel(status)}</span>; }