
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
});
