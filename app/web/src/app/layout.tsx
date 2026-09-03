import "./globals.css";
import type { Metadata } from "next";
import { DeviceProvider } from "@/features/device/DeviceProvider";

export const metadata: Metadata = {
  title: "Aegis-Twin",
  description: "AI-driven cybersecurity fleet dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <DeviceProvider>{children}</DeviceProvider>
        <footer className="site-footer">
          <span>Aegis-Twin IoT Enterprise</span>
          <span>All rights reserved · 2026</span>
        </footer>
      </body>
    </html>
  );
}
