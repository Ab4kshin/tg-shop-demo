import "./polyfills"
import { TonConnectUIProvider } from "@tonconnect/ui-react"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { App } from "./App"
import { ErrorBoundary } from "./components/ErrorBoundary"
import { CurrencyProvider } from "./currency"
import { I18nProvider, useI18n } from "./i18n"
import { CartProvider } from "./store/cart"
import { applyTheme, initTelegram, subscribeTheme } from "./telegram"
import "./styles.css"

initTelegram()
applyTheme()
subscribeTheme()

// Манифест TON Connect раздаётся с корня мини-аппки (public/).
const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`

// Язык TON Connect UI синхронизируем с языком интерфейса магазина.
function Root() {
  const { lang } = useI18n()
  return (
    <TonConnectUIProvider manifestUrl={manifestUrl} language={lang}>
      <CartProvider>
        <App />
      </CartProvider>
    </TonConnectUIProvider>
  )
}

const container = document.getElementById("root")
if (container) {
  createRoot(container).render(
    <StrictMode>
      <ErrorBoundary>
        <I18nProvider>
          <CurrencyProvider>
            <Root />
          </CurrencyProvider>
        </I18nProvider>
      </ErrorBoundary>
    </StrictMode>,
  )
}
