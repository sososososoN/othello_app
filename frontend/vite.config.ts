
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Viteの設定
export default defineConfig({
  plugins: [
    react(),       // Reactの開発支援
    tailwindcss(), // Tailwind CSS v4を有効化
  ],
});
