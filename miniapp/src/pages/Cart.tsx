import { useEffect, useState } from "react"
import { claimPaid, createOrder, fetchPaymentMethods } from "../api"
import { CartItemRow } from "../components/CartItemRow"
import { PaymentInstructions } from "../components/PaymentInstructions"
import { PaymentMethodPicker } from "../components/PaymentMethodPicker"
import { TonPaymentPanel } from "../components/TonPaymentPanel"
import { useCurrency } from "../currency"
import { useI18n } from "../i18n"
import { useCart } from "../store/cart"
import { openPayment } from "../telegram"
import type { ManualInstructions, PaymentMethod, TonPayment } from "../types"

interface Props {
  onGoCatalog: () => void
  onDone: () => void
}

export function Cart({ onGoCatalog, onDone }: Props) {
  const { t } = useI18n()
  const { format } = useCurrency()
  const { lines, setQty, remove, totalKopecks, clear } = useCart()
  const [methods, setMethods] = useState<PaymentMethod[]>([])
  const [method, setMethod] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [instructions, setInstructions] = useState<ManualInstructions | null>(
    null,
  )
  const [tonPayment, setTonPayment] = useState<TonPayment | null>(null)
  const [manualOrderId, setManualOrderId] = useState<number | null>(null)
  const [claimed, setClaimed] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchPaymentMethods()
      .then((data) => {
        setMethods(data)
        if (data.length > 0) setMethod(data[0].id)
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  async function copyDetails() {
    if (!instructions) return
    try {
      await navigator.clipboard.writeText(instructions.details)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* буфер обмена может быть недоступен — просто игнорируем */
    }
  }

  async function onClaim() {
    if (manualOrderId == null) return
    setLoading(true)
    setError(null)
    try {
      await claimPaid(manualOrderId)
      setClaimed(true)
      clear()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function checkout() {
    if (!method) return
    setLoading(true)
    setError(null)
    try {
      const items = lines.map((line) => ({
        product_id: line.product.id,
        qty: line.qty,
      }))
      const result = await createOrder(items, method)
      if (result.kind === "redirect" && result.confirmation_url) {
        openPayment(result.confirmation_url)
        onDone()
      } else if (result.kind === "ton" && result.ton) {
        setTonPayment(result.ton)
      } else if (result.kind === "manual" && result.instructions) {
        setManualOrderId(result.order_id)
        setInstructions(result.instructions)
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (tonPayment) {
    return (
      <TonPaymentPanel payment={tonPayment} onPaid={clear} onDone={onDone} />
    )
  }

  if (instructions) {
    return (
      <PaymentInstructions
        instructions={instructions}
        copied={copied}
        onCopy={copyDetails}
        claimed={claimed}
        loading={loading}
        error={error}
        onClaim={onClaim}
        onDone={onDone}
      />
    )
  }

  if (lines.length === 0) {
    return (
      <div className="page">
        <h1 className="page__title">{t("cart_title")}</h1>
        <p className="hint">{t("cart_empty")}</p>
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={onGoCatalog}
        >
          {t("go_to_catalog")}
        </button>
      </div>
    )
  }

  return (
    <div className="page">
      <h1 className="page__title">{t("cart_title")}</h1>
      <div className="cart-list">
        {lines.map((line) => (
          <CartItemRow
            key={line.product.id}
            line={line}
            onQtyChange={(qty) => setQty(line.product.id, qty)}
            onRemove={() => remove(line.product.id)}
          />
        ))}
      </div>

      <div className="cart-total">
        <span>{t("total")}</span>
        <strong>{format(totalKopecks)}</strong>
      </div>

      <PaymentMethodPicker
        methods={methods}
        selected={method}
        onSelect={setMethod}
      />

      {error && <p className="error">{error}</p>}

      {methods.length > 0 && (
        <button
          type="button"
          className="btn btn--primary btn--block"
          disabled={loading || !method}
          onClick={checkout}
        >
          {loading ? t("creating_order") : t("checkout")}
        </button>
      )}
    </div>
  )
}
