import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#0f172a",
        ink: "#111827",
        slate: "#1f2937",
        accent: "#6366f1",
      },
    },
  },
  plugins: [],
};

export default config;
