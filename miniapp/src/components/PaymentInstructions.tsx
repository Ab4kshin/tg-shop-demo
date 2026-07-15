import { useCurrency } from "../currency"
import { useI18n } from "../i18n"
import type { ManualInstructions } from "../types"

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
  const { t } = useI18n()
  const { format } = useCurrency()
  return (
    <div className="page">
      <h1 className="page__title">{instructions.title}</h1>
      <div className="pay-amount">
        {t("to_pay")} <strong>{format(instructions.amount_kopecks)}</strong>
      </div>
      {instructions.qr_svg && (
        <div className="pay-qr">
          <img src={instructions.qr_svg} alt="QR" />
        </div>
      )}
      <pre className="pay-details">{instructions.details}</pre>
      <button type="button" className="btn btn--block" onClick={onCopy}>
        {copied ? t("copied") : t("copy_details")}
      </button>
      {error && <p className="error">{error}</p>}
      {claimed ? (
        <>
          <div className="pay-note">{t("claimed_note")}</div>
          <button
            type="button"
            className="btn btn--primary btn--block"
            onClick={onDone}
          >
            {t("to_my_orders")}
          </button>
        </>
      ) : (
        <button
          type="button"
          className="btn btn--primary btn--block"
          disabled={loading}
          onClick={onClaim}
        >
          {loading ? t("sending") : t("i_paid")}
        </button>
      )}
    </div>
  )
}
