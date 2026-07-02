import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { App } from "./App"
import { CartProvider } from "./store/cart"
import { applyTheme, initTelegram, subscribeTheme } from "./telegram"
import "./styles.css"

initTelegram()
applyTheme()
subscribeTheme()

const container = document.getElementById("root")
if (container) {
  createRoot(container).render(
    <StrictMode>
      <CartProvider>
        <App />
      </CartProvider>
    </StrictMode>,
  )
}
