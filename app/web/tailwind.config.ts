import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "var(--color-primary)",
          secondary: "var(--color-secondary)",
          accent: "var(--color-accent)",
          success: "var(--color-success)",
          danger: "var(--color-danger)",
          panel: "var(--color-panel)",
          surface: "var(--color-surface)"
        }
      },
      boxShadow: {
        glow: "0 0 24px rgba(44, 140, 255, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;
