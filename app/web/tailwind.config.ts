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
          secondary: "var(--color-complementary)",
          accent: "var(--color-accent)",
          success: "var(--color-success)",
          danger: "var(--color-danger)",
          panel: "var(--color-surface)",
          surface: "var(--color-surface)"
        }
      },
      boxShadow: {
        glow: "0 0 24px var(--color-shadow)"
      }
    }
  },
  plugins: []
};

export default config;
