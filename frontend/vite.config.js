import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // @react-pdf/renderer is large by design; the warning is expected.
  build: { chunkSizeWarningLimit: 2000 },
  server: {
    proxy: {
      "/api": process.env.API_URL || "http://127.0.0.1:8000",
    },
  },
});
