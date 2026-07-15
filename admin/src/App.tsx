import { useState } from "react"
import { clearToken, getToken } from "./api"
import { CurrencySwitch } from "./components/CurrencySwitch"
import { LangSwitch } from "./components/LangSwitch"
import { ThemeToggle } from "./components/ThemeToggle"
import { useI18n } from "./i18n"
import { Login } from "./pages/Login"
import { Orders } from "./pages/Orders"
import { Products } from "./pages/Products"
import { Stats } from "./pages/Stats"

type Tab = "orders" | "products" | "stats"

export function App() {
  const { t } = useI18n()
  const [authed, setAuthed] = useState<boolean>(() => Boolean(getToken()))
  const [tab, setTab] = useState<Tab>("orders")

  if (!authed) {
    return <Login onSuccess={() => setAuthed(true)} />
  }

  function logout() {
    clearToken()
    setAuthed(false)
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          🛍️ TG Shop
          <span>{t("brand_sub")}</span>
        </div>
        <nav className="sidebar__nav">
          <button
            className={tab === "orders" ? "is-active" : ""}
            onClick={() => setTab("orders")}
          >
            {t("nav_orders")}
          </button>
          <button
            className={tab === "products" ? "is-active" : ""}
            onClick={() => setTab("products")}
          >
            {t("nav_products")}
          </button>
          <button
            className={tab === "stats" ? "is-active" : ""}
            onClick={() => setTab("stats")}
          >
            {t("nav_stats")}
          </button>
        </nav>
        <div className="sidebar__footer">
          <CurrencySwitch />
          <LangSwitch />
          <ThemeToggle />
          <button className="sidebar__logout" onClick={logout}>
            {t("logout")}
          </button>
        </div>
      </aside>
      <main className="content">
        {tab === "orders" && <Orders />}
        {tab === "products" && <Products />}
        {tab === "stats" && <Stats />}
      </main>
    </div>
  )
}
