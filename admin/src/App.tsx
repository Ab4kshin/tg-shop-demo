import { useState } from "react"
import { clearToken, getToken } from "./api"
import { Login } from "./pages/Login"
import { Orders } from "./pages/Orders"
import { Products } from "./pages/Products"
import { Stats } from "./pages/Stats"

type Tab = "orders" | "products" | "stats"

export function App() {
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
          <span>админка</span>
        </div>
        <nav className="sidebar__nav">
          <button
            className={tab === "orders" ? "is-active" : ""}
            onClick={() => setTab("orders")}
          >
            Заказы
          </button>
          <button
            className={tab === "products" ? "is-active" : ""}
            onClick={() => setTab("products")}
          >
            Товары
          </button>
          <button
            className={tab === "stats" ? "is-active" : ""}
            onClick={() => setTab("stats")}
          >
            Аналитика
          </button>
        </nav>
        <button className="sidebar__logout" onClick={logout}>
          Выйти
        </button>
      </aside>
      <main className="content">
        {tab === "orders" && <Orders />}
        {tab === "products" && <Products />}
        {tab === "stats" && <Stats />}
      </main>
    </div>
  )
}
