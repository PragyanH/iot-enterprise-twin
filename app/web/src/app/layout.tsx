import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aegis-Twin",
  description: "AI-driven cybersecurity fleet dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
