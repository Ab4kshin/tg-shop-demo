import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { createProduct, fetchProducts, updateProduct } from "../api"
import { ProductForm } from "../components/ProductForm"
import { ProductsTable } from "../components/ProductsTable"
import { CATEGORIES } from "../types"
import type { Product, ProductInput } from "../types"

const EMPTY: ProductInput = {
  title: "",
  description: "",
  price_kopecks: 0,
  photo_url: "",
  category: CATEGORIES[0],
  is_active: true,
}

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState<ProductInput>(EMPTY)
  const [priceRub, setPriceRub] = useState("0")

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

  useEffect(() => {
    load()
  }, [])

  function startNew() {
    setEditing(null)
    setForm(EMPTY)
    setPriceRub("0")
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
    setPriceRub((product.price_kopecks / 100).toString())
  }

  async function save(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const payload: ProductInput = {
      ...form,
      price_kopecks: Math.round(parseFloat(priceRub || "0") * 100),
    }
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

  return (
    <div className="page">
      <div className="page__head">
        <h1>Товары</h1>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="products-layout">
        <div className="table-wrap">
          {loading ? (
            <p className="muted">Загрузка…</p>
          ) : (
            <ProductsTable
              products={products}
              onEdit={startEdit}
              onToggle={toggleActive}
            />
          )}
        </div>
        <ProductForm
          editingId={editing?.id ?? null}
          form={form}
          onChange={setForm}
          priceRub={priceRub}
          onPriceRubChange={setPriceRub}
          onSubmit={save}
          onCancel={startNew}
        />
      </div>
    </div>
  )
}
