import { useCurrency } from "../currency"

export function CurrencySwitch() {
  const { currencies, currency, setCurrency } = useCurrency()
  return (
    <div className="cur-switch">
      {currencies.map((c) => (
        <button
          key={c.code}
          type="button"
          className={`cur-switch__btn ${currency.code === c.code ? "is-active" : ""}`}
          onClick={() => setCurrency(c.code)}
          title={c.code}
        >
          {c.symbol}
        </button>
      ))}
    </div>
  )
}
