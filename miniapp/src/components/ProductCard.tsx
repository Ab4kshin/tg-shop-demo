import type { CSSProperties } from "react"
import { useCurrency } from "../currency"
import { categoryLabel, useI18n } from "../i18n"
import { useCart } from "../store/cart"
import type { Product } from "../types"

export function ProductCard({ product }: { product: Product }) {
  const { add } = useCart()
  const { lang, t } = useI18n()
  const { format } = useCurrency()
  const imageStyle: CSSProperties = {
    backgroundImage: `url(${product.photo_url})`,
  }
  return (
    <div className="card">
      <div className="card__image" style={imageStyle} />
      <div className="card__body">
        <div className="card__category">
          {categoryLabel(lang, product.category)}
        </div>
        <div className="card__title">{product.title}</div>
        <div className="card__price">{format(product.price_kopecks)}</div>
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={() => add(product)}
        >
          {t("add_to_cart")}
        </button>
      </div>
    </div>
  )
}
