// Доступ к Telegram WebApp API (telegram-web-app.js подключается в index.html).
interface TgWebApp {
  initData: string
  colorScheme: "light" | "dark"
  themeParams: Record<string, string>
  viewportHeight?: number
  viewportStableHeight?: number
  initDataUnsafe?: { user?: { language_code?: string } }
  ready: () => void
  expand: () => void
  openLink: (url: string) => void
  onEvent: (event: string, cb: () => void) => void
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TgWebApp }
  }
}

export function tg(): TgWebApp | undefined {
  return window.Telegram?.WebApp
}

export function initTelegram(): void {
  const app = tg()
  if (!app) return
  app.ready()
  app.expand()
  syncViewport()
  app.onEvent("viewportChanged", syncViewport)
}

// Привязываем высоту приложения к стабильной высоте вьюпорта Telegram.
// Без этого на десктопе/Mac 100dvh больше видимой области и таббар «съезжает».
export function syncViewport(): void {
  const app = tg()
  if (!app) return
  const h = app.viewportStableHeight || app.viewportHeight
  if (h && h > 0) {
    document.documentElement.style.setProperty("--app-height", `${h}px`)
  }
}

export function getInitData(): string {
  return tg()?.initData ?? ""
}

// Язык пользователя из Telegram (например, "ru", "en") — для выбора языка по умолчанию.
export function getLanguageCode(): string {
  return tg()?.initDataUnsafe?.user?.language_code ?? ""
}

// Переносим тему Telegram в CSS-переменные --tg-theme-*.
export function applyTheme(): void {
  const app = tg()
  if (!app) return
  const root = document.documentElement
  const params = app.themeParams || {}
  for (const [key, value] of Object.entries(params)) {
    root.style.setProperty(`--tg-theme-${key.replace(/_/g, "-")}`, String(value))
  }
  root.style.setProperty("color-scheme", app.colorScheme || "light")
}

export function subscribeTheme(): void {
  tg()?.onEvent("themeChanged", applyTheme)
}

export function openPayment(url: string): void {
  const app = tg()
  if (app?.openLink) app.openLink(url)
  else window.open(url, "_blank")
}
