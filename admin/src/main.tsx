import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { App } from "./App"
import { CurrencyProvider } from "./currency"
import { I18nProvider } from "./i18n"
import { ThemeProvider } from "./theme"
import "./styles.css"

const container = document.getElementById("root")
if (container) {
  createRoot(container).render(
    <StrictMode>
      <ThemeProvider>
        <I18nProvider>
          <CurrencyProvider>
            <App />
          </CurrencyProvider>
        </I18nProvider>
      </ThemeProvider>
    </StrictMode>,
  )
}
