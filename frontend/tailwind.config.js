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
        dark: {
          950: "#03071a",
          900: "#060d1e",
          800: "#0a1628",
          700: "#0f1f38",
          600: "#152846",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card:               "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 4px 12px 0 rgb(0 0 0 / 0.04)",
        "card-hover":       "0 4px 8px 0 rgb(0 0 0 / 0.08), 0 12px 24px 0 rgb(0 0 0 / 0.06)",
        "glow-brand":       "0 0 0 3px rgb(37 99 235 / 0.15)",
        "glow-blue":        "0 0 32px rgba(59,130,246,0.45), 0 0 64px rgba(59,130,246,0.15)",
        "glow-blue-sm":     "0 0 14px rgba(59,130,246,0.35)",
        "card-dark":        "0 1px 0 0 rgba(255,255,255,0.04), 0 4px 24px 0 rgba(0,0,0,0.5)",
        "card-dark-hover":  "0 0 0 1px rgba(59,130,246,0.35), 0 8px 32px rgba(0,0,0,0.5), 0 0 24px rgba(59,130,246,0.15)",
      },
      backgroundImage: {
        "dot-dark":      "radial-gradient(circle, rgba(255,255,255,0.055) 1px, transparent 1px)",
        "dot-grid":      "radial-gradient(circle, rgb(30 41 59) 1px, transparent 1px)",
        "hero-fade":     "linear-gradient(to bottom, transparent 60%, rgb(4 9 26) 100%)",
        "blue-glow":     "radial-gradient(ellipse at center, rgba(59,130,246,0.28) 0%, transparent 68%)",
        "blue-glow-sm":  "radial-gradient(ellipse at center, rgba(59,130,246,0.18) 0%, transparent 65%)",
      },
      backgroundSize: {
        "dot-32": "32px 32px",
        "dot-28": "28px 28px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float":      "float 7s ease-in-out infinite",
        "orb-1":      "orb1 12s ease-in-out infinite",
        "orb-2":      "orb2 16s ease-in-out infinite",
        "shimmer":    "shimmer 2.4s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-12px)" },
        },
        orb1: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)",         opacity: "0.55" },
          "40%":      { transform: "translate(40px, -30px) scale(1.08)", opacity: "0.75" },
          "70%":      { transform: "translate(-25px, 20px) scale(0.94)", opacity: "0.45" },
        },
        orb2: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)",          opacity: "0.4" },
          "35%":      { transform: "translate(-50px, 30px) scale(1.12)", opacity: "0.6" },
          "65%":      { transform: "translate(35px, -20px) scale(0.9)",  opacity: "0.35" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition:  "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
