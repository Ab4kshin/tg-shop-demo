import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // fs.allow нужен, чтобы dev-сервер видел общий ../../shared/types
  server: { port: 5173, fs: { allow: [".."] } },
})
