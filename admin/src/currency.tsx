import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"
import type { ReactNode } from "react"
import { fetchCurrencies } from "./api"
import type { Currency } from "./types"

const STORAGE_KEY = "tg-shop-admin-currency"

// Цены в БД хранятся в рублях (копейках). Резервные курсы на случай,
// если бэкенд не ответил (rub_per_unit = сколько ₽ стоит 1 единица).
const FALLBACK: Currency[] = [
  { code: "RUB", symbol: "\u20bd", locale: "ru-RU", rub_per_unit: 1 },
  { code: "USD", symbol: "$", locale: "en-US", rub_per_unit: 90 },
  { code: "EUR", symbol: "\u20ac", locale: "de-DE", rub_per_unit: 98 },
]

interface CurrencyValue {
  currencies: Currency[]
  currency: Currency
  setCurrency: (code: string) => void
  format: (kopecks: number) => string
  // Не null, если курсы не загрузились и мы работаем на резервных (UI может предупредить).
  ratesError: string | null
}

const CurrencyContext = createContext<CurrencyValue | null>(null)

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currencies, setCurrencies] = useState<Currency[]>(FALLBACK)
  const [ratesError, setRatesError] = useState<string | null>(null)
  const [code, setCode] = useState<string>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || "RUB"
    } catch {
      return "RUB"
    }
  })

  useEffect(() => {
    let active = true
    fetchCurrencies()
      .then((list) => {
        if (!active) return
        if (list.length) setCurrencies(list)
        setRatesError(null)
      })
      .catch((err: unknown) => {
        if (!active) return
        // Явно фиксируем деградацию: остаёмся на FALLBACK-курсах, но
        // сообщаем об этом через ratesError, чтобы UI мог показать баннер.
        const message = err instanceof Error ? err.message : String(err)
        console.error("Курсы валют недоступны, использую резервные:", err)
        setRatesError(message)
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, code)
    } catch {
      /* ignore */
    }
  }, [code])

  const currency = useMemo(
    () => currencies.find((c) => c.code === code) || currencies[0],
    [currencies, code],
  )

  const setCurrency = useCallback((c: string) => setCode(c), [])

  const format = useCallback(
    (kopecks: number) => {
      const rub = kopecks / 100
      const amount = rub / (currency.rub_per_unit || 1)
      const digits = currency.code === "RUB" ? 0 : 2
      try {
        return new Intl.NumberFormat(currency.locale, {
          style: "currency",
          currency: currency.code,
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        }).format(amount)
      } catch {
        return `${amount.toFixed(digits)}\u00a0${currency.symbol}`
      }
    },
    [currency],
  )

  const value = useMemo<CurrencyValue>(
    () => ({ currencies, currency, setCurrency, format, ratesError }),
    [currencies, currency, setCurrency, format, ratesError],
  )
  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  )
}

export function useCurrency(): CurrencyValue {
  const ctx = useContext(CurrencyContext)
  if (!ctx) throw new Error("useCurrency must be used within CurrencyProvider")
  return ctx
}
