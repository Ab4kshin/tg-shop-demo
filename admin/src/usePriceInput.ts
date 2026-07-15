import { useEffect, useRef, useState } from "react"
import type { Currency } from "./types"

// Хранит цену в единицах выбранной валюты и пересчитывает её при смене
// валюты, чтобы значение поля не «прыгало» (база хранения — рубли).
export function usePriceInput(currency: Currency) {
  const [priceValue, setPriceValue] = useState("0")
  const prevCurrency = useRef(currency)

  useEffect(() => {
    const prev = prevCurrency.current
    if (prev.code === currency.code) return
    setPriceValue((cur) => {
      const val = parseFloat(cur || "0")
      const rub = val * (prev.rub_per_unit || 1)
      const next = rub / (currency.rub_per_unit || 1)
      return String(Number(next.toFixed(2)))
    })
    prevCurrency.current = currency
  }, [currency])

  return { priceValue, setPriceValue }
}
