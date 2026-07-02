import { useCart } from "../store/cart"
import type { Product } from "../types"
import { formatPrice } from "../utils"

export function ProductCard({ product }: { product: Product }) {
  const { add } = useCart()
  return (
    <div className="card">
      <div
        className="card__image"
        style={{ backgroundImage: `url(${product.photo_url})` }}
      />
      <div className="card__body">
        <div className="card__category">{product.category}</div>
        <div className="card__title">{product.title}</div>
        <div className="card__price">{formatPrice(product.price_kopecks)}</div>
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={() => add(product)}
        >
          В корзину
        </button>
      </div>
    </div>
  )
}
