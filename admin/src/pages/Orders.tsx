import { useEffect, useState } from "react"
import { fetchOrders, updateOrderStatus } from "../api"
import { useCurrency } from "../currency"
import { methodLabel, statusLabel, useI18n } from "../i18n"
import { STATUSES } from "../types"
import type { AdminOrder } from "../types"

export function Orders() {
  const { lang, t } = useI18n()
  const { format } = useCurrency()
  const [orders, setOrders] = useState<AdminOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setOrders(await fetchOrders())
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function change(id: number, status: string) {
    try {
      await updateOrderStatus(id, status)
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="page">
      <div className="page__head">
        <h1>{t("orders_title")}</h1>
        <button className="btn" onClick={load}>
          {t("refresh")}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? (
        <p className="muted">{t("loading")}</p>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t("col_num")}</th>
                <th>{t("col_customer")}</th>
                <th>{t("col_items")}</th>
                <th>{t("col_method")}</th>
                <th>{t("col_amount")}</th>
                <th>{t("col_status")}</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>
                    {order.user_name}
                    <div className="muted small">tg:{order.user_tg_id}</div>
                  </td>
                  <td className="cell-items">
                    {order.items
                      .map((item) => `${item.title} ×${item.qty}`)
                      .join(", ")}
                  </td>
                  <td>{methodLabel(lang, order.payment_method)}</td>
                  <td>{format(order.total_kopecks)}</td>
                  <td>
                    <select
                      value={order.status}
                      onChange={(e) => change(order.id, e.target.value)}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {statusLabel(lang, s)}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    {t("no_orders")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
