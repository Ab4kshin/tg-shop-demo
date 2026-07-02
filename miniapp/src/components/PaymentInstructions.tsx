import type { ManualInstructions } from "../types"
import { formatPrice } from "../utils"

interface Props {
  instructions: ManualInstructions
  copied: boolean
  onCopy: () => void
  claimed: boolean
  loading: boolean
  error: string | null
  onClaim: () => void
  onDone: () => void
}

export function PaymentInstructions({
  instructions,
  copied,
  onCopy,
  claimed,
  loading,
  error,
  onClaim,
  onDone,
}: Props) {
  return (
    <div className="page">
      <h1 className="page__title">{instructions.title}</h1>
      <div className="pay-amount">
        К оплате: <strong>{formatPrice(instructions.amount_kopecks)}</strong>
      </div>
      {instructions.qr_svg && (
        <div className="pay-qr">
          <img src={instructions.qr_svg} alt="QR" />
        </div>
      )}
      <pre className="pay-details">{instructions.details}</pre>
      <button type="button" className="btn btn--block" onClick={onCopy}>
        {copied ? "Скопировано ✓" : "📋 Скопировать реквизиты"}
      </button>
      {error && <p className="error">{error}</p>}
      {claimed ? (
        <>
          <div className="pay-note">
            ✅ Спасибо! Мы проверим поступление и подтвердим заказ. Статус — в
            разделе «Заказы».
          </div>
          <button
            type="button"
            className="btn btn--primary btn--block"
            onClick={onDone}
          >
            К моим заказам
          </button>
        </>
      ) : (
        <button
          type="button"
          className="btn btn--primary btn--block"
          disabled={loading}
          onClick={onClaim}
        >
          {loading ? "Отправляем…" : "Я оплатил"}
        </button>
      )}
    </div>
  )
}
