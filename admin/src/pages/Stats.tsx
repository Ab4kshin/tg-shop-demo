import { useEffect, useState } from "react"
import { fetchStats } from "../api"
import type { Stats as StatsType } from "../types"
import { formatPrice } from "../utils"

export function Stats() {
  const [stats, setStats] = useState<StatsType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((e: Error) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="page">
        <h1>Аналитика</h1>
        <div className="error">{error}</div>
      </div>
    )
  }
  if (!stats) {
    return (
      <div className="page">
        <h1>Аналитика</h1>
        <p className="muted">Загрузка…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page__head">
        <h1>Аналитика</h1>
      </div>
      <div className="cards">
        <div className="stat-card">
          <div className="stat-card__label">Всего заказов</div>
          <div className="stat-card__value">{stats.total_orders}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Оплачено</div>
          <div className="stat-card__value">{stats.paid_orders}</div>
        </div>
        <div className="stat-card stat-card--accent">
          <div className="stat-card__label">Выручка</div>
          <div className="stat-card__value">
            {formatPrice(stats.revenue_kopecks)}
          </div>
        </div>
      </div>
      <h2 className="section-title">Топ товаров</h2>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Товар</th>
              <th>Продано</th>
              <th>Выручка</th>
            </tr>
          </thead>
          <tbody>
            {stats.top_products.map((t) => (
              <tr key={t.id}>
                <td>{t.title}</td>
                <td>{t.qty}</td>
                <td>{formatPrice(t.revenue_kopecks)}</td>
              </tr>
            ))}
            {stats.top_products.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  Пока нет оплаченных заказов.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
