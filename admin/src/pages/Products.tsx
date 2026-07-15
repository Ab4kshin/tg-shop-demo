import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import {
  createCategory,
  createProduct,
  deleteCategory,
  deleteProduct,
  fetchCategories,
  fetchProducts,
  updateProduct,
} from "../api"
import { CategoryManager } from "../components/CategoryManager"
import { ProductForm } from "../components/ProductForm"
import { ProductsTable } from "../components/ProductsTable"
import { useCurrency } from "../currency"
import { useI18n } from "../i18n"
import { CATEGORIES } from "../types"
import type { Currency, Product, ProductInput } from "../types"
import { usePriceInput } from "../usePriceInput"

const EMPTY: ProductInput = {
  title: "",
  description: "",
  price_kopecks: 0,
  photo_url: "",
  category: CATEGORIES[0],
  is_active: true,
}

// Копейки (база — рубли) -> строка в выбранной валюте для поля ввода.
function kopecksToInput(kopecks: number, cur: Currency): string {
  const amount = kopecks / 100 / (cur.rub_per_unit || 1)
  return String(Number(amount.toFixed(2)))
}

export function Products() {
  const { t } = useI18n()
  const { currency } = useCurrency()
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<string[]>([...CATEGORIES])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState<ProductInput>(EMPTY)
  const { priceValue, setPriceValue } = usePriceInput(currency)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setProducts(await fetchProducts())
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function loadCategories() {
    try {
      const list = await fetchCategories()
      if (list.length) setCategories(list)
    } catch {
      /* оставляем дефолтные категории */
    }
  }

  useEffect(() => {
    load()
    loadCategories()
  }, [])

  function startNew() {
    setEditing(null)
    setForm({ ...EMPTY, category: categories[0] ?? EMPTY.category })
    setPriceValue("0")
  }

  function startEdit(product: Product) {
    setEditing(product)
    setForm({
      title: product.title,
      description: product.description,
      price_kopecks: product.price_kopecks,
      photo_url: product.photo_url,
      category: product.category,
      is_active: product.is_active,
    })
    setPriceValue(kopecksToInput(product.price_kopecks, currency))
  }

  async function save(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const kopecks = Math.round(
      parseFloat(priceValue || "0") * (currency.rub_per_unit || 1) * 100,
    )
    const payload: ProductInput = { ...form, price_kopecks: kopecks }
    try {
      if (editing) await updateProduct(editing.id, payload)
      else await createProduct(payload)
      startNew()
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function toggleActive(product: Product) {
    try {
      await updateProduct(product.id, { is_active: !product.is_active })
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function removeProduct(product: Product) {
    if (!window.confirm(t("del_confirm"))) return
    setError(null)
    try {
      await deleteProduct(product.id)
      if (editing?.id === product.id) startNew()
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function addCategory(name: string) {
    setError(null)
    try {
      await createCategory(name)
      await loadCategories()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function removeCategory(name: string) {
    setError(null)
    try {
      await deleteCategory(name)
      await loadCategories()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="page">
      <div className="page__head">
        <h1>{t("products_title")}</h1>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="products-layout">
        <div className="table-wrap">
          {loading ? (
            <p className="muted">{t("loading")}</p>
          ) : (
            <ProductsTable
              products={products}
              onEdit={startEdit}
              onToggle={toggleActive}
              onDelete={removeProduct}
            />
          )}
        </div>
        <div className="products-side">
          <ProductForm
            editingId={editing?.id ?? null}
            form={form}
            categories={categories}
            onChange={setForm}
            priceValue={priceValue}
            currencySymbol={currency.symbol}
            onPriceChange={setPriceValue}
            onSubmit={save}
            onCancel={startNew}
          />
          <CategoryManager
            categories={categories}
            onAdd={addCategory}
            onDelete={removeCategory}
          />
        </div>
      </div>
    </div>
  )
}
