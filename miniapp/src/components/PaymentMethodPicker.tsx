import { METHOD_LABELS, useI18n } from "../i18n"
import type { PaymentMethod } from "../types"

interface Props {
  methods: PaymentMethod[]
  selected: string | null
  onSelect: (id: string) => void
}

export function PaymentMethodPicker({ methods, selected, onSelect }: Props) {
  const { lang, t } = useI18n()
  if (methods.length === 0) {
    return <p className="hint">{t("methods_none")}</p>
  }
  return (
    <div className="methods">
      <div className="methods__title">{t("payment_method")}</div>
      {methods.map((m) => {
        const override = METHOD_LABELS[lang][m.id]
        const title = override?.title ?? m.title
        const description = override?.description ?? m.description
        return (
          <button
            key={m.id}
            type="button"
            className={`method ${selected === m.id ? "method--active" : ""}`}
            onClick={() => onSelect(m.id)}
          >
            <span className="method__title">{title}</span>
            <span className="method__desc">{description}</span>
          </button>
        )
      })}
    </div>
  )
}
