import { useEffect, useState } from "react"
import { fetchStats } from "../api"
import { useCurrency } from "../currency"
import { useI18n } from "../i18n"
import type { Stats as StatsType } from "../types"

export function Stats() {
  const { t } = useI18n()
  const { format } = useCurrency()
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
        <h1>{t("stats_title")}</h1>
        <div className="error">{error}</div>
      </div>
    )
  }
  if (!stats) {
    return (
      <div className="page">
        <h1>{t("stats_title")}</h1>
        <p className="muted">{t("loading")}</p>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page__head">
        <h1>{t("stats_title")}</h1>
      </div>
      <div className="cards">
        <div className="stat-card">
          <div className="stat-card__label">{t("stat_total_orders")}</div>
          <div className="stat-card__value">{stats.total_orders}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">{t("stat_paid")}</div>
          <div className="stat-card__value">{stats.paid_orders}</div>
        </div>
        <div className="stat-card stat-card--accent">
          <div className="stat-card__label">{t("stat_revenue")}</div>
          <div className="stat-card__value">
            {format(stats.revenue_kopecks)}
          </div>
        </div>
      </div>
      <h2 className="section-title">{t("top_products")}</h2>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>{t("col_product")}</th>
              <th>{t("th_sold")}</th>
              <th>{t("th_revenue")}</th>
            </tr>
          </thead>
          <tbody>
            {stats.top_products.map((item) => (
              <tr key={item.id}>
                <td>{item.title}</td>
                <td>{item.qty}</td>
                <td>{format(item.revenue_kopecks)}</td>
              </tr>
            ))}
            {stats.top_products.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  {t("no_paid")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
