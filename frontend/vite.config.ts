import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// FastAPIの接続先
const apiTarget = "http://127.0.0.1:5001";

export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },

  server: {
    proxy: {
      "/state": apiTarget,
      "/games": apiTarget,
      "/moves": apiTarget,
      "/reset": apiTarget,
      "/analysis": apiTarget,
      "/mode": apiTarget,
      "/difficulty": apiTarget,
    },
  },
});
