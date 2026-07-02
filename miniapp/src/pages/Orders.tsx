import { useEffect, useState } from "react"
import { fetchMyOrders } from "../api"
import type { Order } from "../types"
import { formatPrice, STATUS_LABELS } from "../utils"

export function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetchMyOrders()
      .then((data) => {
        if (active) setOrders(data)
      })
      .catch((e: Error) => {
        if (active) setError(e.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="page">
      <h1 className="page__title">Мои заказы</h1>
      {loading && <p className="hint">Загрузка…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="hint">Заказов пока нет.</p>
      )}
      <div className="orders">
        {orders.map((order) => (
          <div className="order" key={order.id}>
            <div className="order__head">
              <span className="order__id">Заказ №{order.id}</span>
              <span className={`status status--${order.status}`}>
                {STATUS_LABELS[order.status] ?? order.status}
              </span>
            </div>
            <div className="order__items">
              {order.items.map((item) => (
                <div className="order__item" key={item.product_id}>
                  <span>
                    {item.title} × {item.qty}
                  </span>
                  <span>
                    {formatPrice(item.price_at_purchase_kopecks * item.qty)}
                  </span>
                </div>
              ))}
            </div>
            <div className="order__total">
              <span>Итого</span>
              <strong>{formatPrice(order.total_kopecks)}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
