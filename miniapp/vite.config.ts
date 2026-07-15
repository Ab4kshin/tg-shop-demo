import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // TON-библиотеки (@ton/core, @tonconnect/*) обращаются к node-глобалям
  // (global / process). В браузере их нет → без этого мини-аппка падает
  // в пустой экран. Полифиллы Buffer/process/global — в src/polyfills.ts.
  define: {
    global: "globalThis",
    "process.env": "{}",
  },
  optimizeDeps: { include: ["buffer"] },
  // fs.allow нужен, чтобы dev-сервер видел общий ../../shared/types
  server: { port: 5173, fs: { allow: [".."] } },
})
