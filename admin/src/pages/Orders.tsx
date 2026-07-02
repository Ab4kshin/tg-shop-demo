import { useEffect, useState } from "react"
import { fetchOrders, updateOrderStatus } from "../api"
import { STATUSES } from "../types"
import type { AdminOrder } from "../types"
import { formatPrice, METHOD_LABELS, STATUS_LABELS } from "../utils"

export function Orders() {
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
        <h1>Заказы</h1>
        <button className="btn" onClick={load}>
          Обновить
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? (
        <p className="muted">Загрузка…</p>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>№</th>
                <th>Покупатель</th>
                <th>Состав</th>
                <th>Способ</th>
                <th>Сумма</th>
                <th>Статус</th>
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
                  <td>{METHOD_LABELS[order.payment_method] ?? order.payment_method}</td>
                  <td>{formatPrice(order.total_kopecks)}</td>
                  <td>
                    <select
                      value={order.status}
                      onChange={(e) => change(order.id, e.target.value)}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {STATUS_LABELS[s]}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    Заказов нет.
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
