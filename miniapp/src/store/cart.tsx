import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"
import type { ReactNode } from "react"
import type { Product } from "../types"

export interface CartLine {
  product: Product
  qty: number
}

interface CartContextValue {
  lines: CartLine[]
  add: (product: Product) => void
  setQty: (productId: number, qty: number) => void
  remove: (productId: number) => void
  clear: () => void
  totalKopecks: number
  count: number
}

const CartContext = createContext<CartContextValue | null>(null)
const STORAGE_KEY = "tg-shop-cart"

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? (JSON.parse(raw) as CartLine[]) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(lines))
    } catch {
      /* ignore */
    }
  }, [lines])

  const add = useCallback((product: Product) => {
    setLines((prev) => {
      const existing = prev.find((line) => line.product.id === product.id)
      if (existing) {
        return prev.map((line) =>
          line.product.id === product.id
            ? { ...line, qty: Math.min(line.qty + 1, 99) }
            : line,
        )
      }
      return [...prev, { product, qty: 1 }]
    })
  }, [])

  const setQty = useCallback((productId: number, qty: number) => {
    setLines((prev) =>
      prev
        .map((line) =>
          line.product.id === productId
            ? { ...line, qty: Math.min(Math.max(qty, 0), 99) }
            : line,
        )
        .filter((line) => line.qty > 0),
    )
  }, [])

  const remove = useCallback((productId: number) => {
    setLines((prev) => prev.filter((line) => line.product.id !== productId))
  }, [])

  const clear = useCallback(() => setLines([]), [])

  const totalKopecks = useMemo(
    () =>
      lines.reduce((sum, line) => sum + line.product.price_kopecks * line.qty, 0),
    [lines],
  )
  const count = useMemo(
    () => lines.reduce((sum, line) => sum + line.qty, 0),
    [lines],
  )

  const value: CartContextValue = {
    lines,
    add,
    setQty,
    remove,
    clear,
    totalKopecks,
    count,
  }
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error("useCart должен быть внутри CartProvider")
  return ctx
}
