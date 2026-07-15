import { useEffect, useState } from "react"
import { fetchCategories, fetchProducts } from "../api"
import { CategoryTabs } from "../components/CategoryTabs"
import { ProductCard } from "../components/ProductCard"
import { useI18n } from "../i18n"
import { CATEGORIES } from "../types"
import type { Product } from "../types"

export function Catalog() {
  const { t } = useI18n()
  const [category, setCategory] = useState<string | null>(null)
  const [categories, setCategories] = useState<string[]>([...CATEGORIES])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetchCategories()
      .then((data) => {
        if (active && data.length) setCategories(data)
      })
      .catch(() => {
        /* оставляем дефолтные категории */
      })
    return () => {
      active = false
    }
  }, [])

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
      <h1 className="page__title">{t("shop_title")}</h1>
      <CategoryTabs
        categories={categories}
        active={category}
        onChange={setCategory}
      />
      {loading && <p className="hint">{t("loading")}</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && products.length === 0 && (
        <p className="hint">{t("nothing_found")}</p>
      )}
      <div className="grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  )
}
