/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 4px 12px 0 rgb(0 0 0 / 0.04)",
        "card-hover": "0 4px 8px 0 rgb(0 0 0 / 0.08), 0 12px 24px 0 rgb(0 0 0 / 0.06)",
        "glow-brand": "0 0 0 3px rgb(37 99 235 / 0.15)",
      },
      backgroundImage: {
        "dot-grid":
          "radial-gradient(circle, rgb(30 41 59) 1px, transparent 1px)",
        "hero-fade":
          "linear-gradient(to bottom, transparent 60%, rgb(2 6 23) 100%)",
      },
      backgroundSize: {
        "dot-32": "32px 32px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
