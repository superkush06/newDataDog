import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink:    { 950: "#0A0908", 900: "#141210", 800: "#1C1A18", 700: "#252220", 600: "#2A2724" },
        paper:  { DEFAULT: "#F5F1EA", dim: "#A39E94", mute: "#6E6963" },
        signal: { DEFAULT: "#C5F73A", dim: "#7A9920", glow: "rgba(197,247,58,0.18)" },
        alarm:  { DEFAULT: "#FF4D4D", dim: "#9C2A2A", glow: "rgba(255,77,77,0.18)" },
        warn:   { DEFAULT: "#E8A33D", dim: "#8C5C18" },
        cool:   { DEFAULT: "#7CC8FF", dim: "#2E6E9C" },
        reddit: { DEFAULT: "#FF4500", dim: "#7A2300" },
      },
      fontFamily: {
        display: ['"Fraunces"', "ui-serif", "Georgia", "serif"],
        body:    ['"Manrope"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono:    ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      letterSpacing: {
        terminal: "0.18em",
      },
      animation: {
        "pulse-dot": "pulseDot 1.8s cubic-bezier(0.4,0,0.6,1) infinite",
        "ticker":    "ticker 90s linear infinite",
        "shimmer":   "shimmer 2.4s ease-in-out infinite",
        "rise":      "rise 600ms cubic-bezier(0.16,1,0.3,1) both",
      },
      keyframes: {
        pulseDot: {
          "0%,100%": { opacity: "1", transform: "scale(1)" },
          "50%":     { opacity: "0.45", transform: "scale(0.92)" },
        },
        ticker: {
          "0%":   { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        shimmer: {
          "0%,100%": { opacity: "0.55" },
          "50%":     { opacity: "1" },
        },
        rise: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
