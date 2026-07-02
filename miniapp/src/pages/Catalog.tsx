import { useEffect, useState } from "react"
import { fetchProducts } from "../api"
import { CategoryTabs } from "../components/CategoryTabs"
import { ProductCard } from "../components/ProductCard"
import type { Product } from "../types"

export function Catalog() {
  const [category, setCategory] = useState<string | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetchProducts(category ?? undefined)
      .then((data) => {
        if (active) setProducts(data)
      })
      .catch((e: Error) => {
        if (active) setError(e.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [category])

  return (
    <div className="page">
      <h1 className="page__title">Магазин подарков</h1>
      <CategoryTabs active={category} onChange={setCategory} />
      {loading && <p className="hint">Загрузка…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && products.length === 0 && (
        <p className="hint">Ничего не найдено.</p>
      )}
      <div className="grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  )
}
