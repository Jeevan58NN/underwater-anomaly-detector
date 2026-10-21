/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        abyss: {
          950: "#040c14",
          900: "#071620",
          850: "#0a1c29",
          800: "#0e2534",
          700: "#153347",
          600: "#1d4460",
        },
        signal: {
          cyan: "#22d3ee",
          teal: "#2dd4bf",
          blue: "#38bdf8",
        },
        sonar: {
          amber: "#f5b942",
          coral: "#f97066",
          green: "#4ade80",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
        body: ["'Inter'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(34, 211, 238, 0.25)",
        panel: "0 8px 32px rgba(0,0,0,0.45)",
      },
      backgroundImage: {
        "sonar-grid":
          "linear-gradient(rgba(34,211,238,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.06) 1px, transparent 1px)",
      },
      animation: {
        sweep: "sweep 3.2s linear infinite",
        pulseSlow: "pulseSlow 2.4s ease-in-out infinite",
      },
      keyframes: {
        sweep: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        pulseSlow: {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.4 },
        },
      },
    },
  },
  plugins: [],
};
