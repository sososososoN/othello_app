import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // ReactとTailwindを有効にする
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      // @/ は frontend/src/ を指す
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      "/state": "http://127.0.0.1.8000",
      "/games": "http://127.0.0.1.8000",
      "/moves": "http://127.0.0.1.8000",
      "/reset": "http://127.0.0.1.8000",
      "/analysis": "http://127.0.0.1.8000",
      "/mode": "http://127.0.0.1.8000",
      "/difficulty": "http://127.0.0.1.8000",
    },
  },
});
