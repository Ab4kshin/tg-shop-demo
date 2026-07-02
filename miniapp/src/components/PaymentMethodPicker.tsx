import type { PaymentMethod } from "../types"

interface Props {
  methods: PaymentMethod[]
  selected: string | null
  onSelect: (id: string) => void
}

export function PaymentMethodPicker({ methods, selected, onSelect }: Props) {
  if (methods.length === 0) {
    return <p className="hint">Способы оплаты пока не настроены.</p>
  }
  return (
    <div className="methods">
      <div className="methods__title">Способ оплаты</div>
      {methods.map((m) => (
        <button
          key={m.id}
          type="button"
          className={`method ${selected === m.id ? "method--active" : ""}`}
          onClick={() => onSelect(m.id)}
        >
          <span className="method__title">{m.title}</span>
          <span className="method__desc">{m.description}</span>
        </button>
      ))}
    </div>
  )
}
