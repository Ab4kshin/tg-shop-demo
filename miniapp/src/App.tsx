import { useState } from "react"
import { CurrencySwitch } from "./components/CurrencySwitch"
import { LangSwitch } from "./components/LangSwitch"
import { useI18n } from "./i18n"
import { Cart } from "./pages/Cart"
import { Catalog } from "./pages/Catalog"
import { Orders } from "./pages/Orders"
import { useCart } from "./store/cart"

type Tab = "catalog" | "cart" | "orders"

export function App() {
  const [tab, setTab] = useState<Tab>("catalog")
  const { count } = useCart()
  const { t } = useI18n()

  return (
    <div className="app">
      <header className="app__header">
        <span className="app__brand">🛍️ {t("shop_title")}</span>
        <div className="app__controls">
          <CurrencySwitch />
          <LangSwitch />
        </div>
      </header>
      <main className="app__content">
        {tab === "catalog" && <Catalog />}
        {tab === "cart" && (
          <Cart
            onGoCatalog={() => setTab("catalog")}
            onDone={() => setTab("orders")}
          />
        )}
        {tab === "orders" && <Orders />}
      </main>

      <nav className="tabbar">
        <button
          type="button"
          className={`tabbar__item ${tab === "catalog" ? "is-active" : ""}`}
          onClick={() => setTab("catalog")}
        >
          <span className="tabbar__icon">🛍️</span>
          {t("tab_catalog")}
        </button>
        <button
          type="button"
          className={`tabbar__item ${tab === "cart" ? "is-active" : ""}`}
          onClick={() => setTab("cart")}
        >
          <span className="tabbar__icon">
            🛒
            {count > 0 && <span className="badge">{count}</span>}
          </span>
          {t("tab_cart")}
        </button>
        <button
          type="button"
          className={`tabbar__item ${tab === "orders" ? "is-active" : ""}`}
          onClick={() => setTab("orders")}
        >
          <span className="tabbar__icon">📦</span>
          {t("tab_orders")}
        </button>
      </nav>
    </div>
  )
}
