import { useCallback, useEffect, useState } from "react"
import { checkTonPayment, fetchMyOrders } from "../api"
import { useCurrency } from "../currency"
import { statusLabel, useI18n } from "../i18n"
import type { Order } from "../types"

export function Orders() {
  const { lang, t } = useI18n()
  const { format } = useCurrency()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const data = await fetchMyOrders()
    setOrders(data)
    return data
  }, [])

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        const data = await load()
        // Досверяем незавершённые заказы: TON/USDT-оплата могла подтвердиться
        // уже после закрытия экрана оплаты (или если проверка сети сорвалась).
        // Для не-крипто заказов эндпоинт вернёт ошибку — тихо игнорируем.
        const pending = data.filter((o) => o.status === "new")
        if (pending.length > 0) {
          const results = await Promise.all(
            pending.map((o) =>
              checkTonPayment(o.id)
                .then((r) => r.status === "paid")
                .catch(() => false),
            ),
          )
          if (active && results.some(Boolean)) {
            await load()
          }
        }
      } catch (e) {
        if (active) setError((e as Error).message)
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => {
      active = false
    }
  }, [load])

  return (
    <div className="page">
      <h1 className="page__title">{t("my_orders")}</h1>
      {loading && <p className="hint">{t("loading")}</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="hint">{t("no_orders")}</p>
      )}
      <div className="orders">
        {orders.map((order) => (
          <div className="order" key={order.id}>
            <div className="order__head">
              <span className="order__id">{t("order_no", { id: order.id })}</span>
              <span className={`status status--${order.status}`}>
                {statusLabel(lang, order.status)}
              </span>
            </div>
            <div className="order__items">
              {order.items.map((item) => (
                <div className="order__item" key={item.product_id}>
                  <span>
                    {item.title} × {item.qty}
                  </span>
                  <span>
                    {format(item.price_at_purchase_kopecks * item.qty)}
                  </span>
                </div>
              ))}
            </div>
            <div className="order__total">
              <span>{t("total")}</span>
              <strong>{format(order.total_kopecks)}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
