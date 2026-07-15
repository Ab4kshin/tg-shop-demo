import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // Админка отдаётся бэкендом на /admin (single-origin), поэтому base=/admin/.
  base: "/admin/",
  // fs.allow нужен, чтобы dev-сервер видел общий ../../shared/types
  server: { port: 5174, fs: { allow: [".."] } },
})
