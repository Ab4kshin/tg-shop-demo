// Полифиллы node-глобалей для браузера (нужны @ton/core и @tonconnect/*).
// Импортируется ПЕРВЫМ в main.tsx — до TON-библиотек, иначе белый/чёрный экран.
import { Buffer } from "buffer"

const g = globalThis as typeof globalThis & {
  global?: unknown
  Buffer?: unknown
  process?: { env: Record<string, string> }
}

if (typeof g.global === "undefined") g.global = globalThis
if (typeof g.Buffer === "undefined") g.Buffer = Buffer
if (typeof g.process === "undefined") g.process = { env: {} }
