import "./globals.css";
import type { Metadata } from "next";
import { DeviceProvider } from "@/features/device/DeviceProvider";
import { ThemeProvider } from "@/context/ThemeContext";

export const metadata: Metadata = {
  title: "Aegis-Twin",
  description: "AI-driven cybersecurity fleet dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <body>
        <ThemeProvider>
          <DeviceProvider>{children}</DeviceProvider>
          <footer className="site-footer">
            <div className="site-footer-inner">
              <span className="footer-copyright">© 2026 Aegis-Twin</span>
              <span className="footer-dot">•</span>
              <button type="button" className="footer-link">Change cookie settings</button>
              <span className="footer-dot">•</span>
              <a href="#privacy" className="footer-link">Privacy Notice</a>
              <span className="footer-dot">•</span>
              <a href="#provider" className="footer-link">Provider Information</a>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}

