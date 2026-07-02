import type { CartLine } from "../store/cart"
import { formatPrice } from "../utils"

interface Props {
  line: CartLine
  onQtyChange: (qty: number) => void
  onRemove: () => void
}

export function CartItemRow({ line, onQtyChange, onRemove }: Props) {
  return (
    <div className="cart-item">
      <div
        className="cart-item__image"
        style={{ backgroundImage: `url(${line.product.photo_url})` }}
      />
      <div className="cart-item__info">
        <div className="cart-item__title">{line.product.title}</div>
        <div className="cart-item__price">
          {formatPrice(line.product.price_kopecks)}
        </div>
      </div>
      <div className="qty">
        <button
          type="button"
          className="qty__btn"
          onClick={() => onQtyChange(line.qty - 1)}
        >
          −
        </button>
        <span className="qty__value">{line.qty}</span>
        <button
          type="button"
          className="qty__btn"
          onClick={() => onQtyChange(line.qty + 1)}
        >
          +
        </button>
      </div>
      <button
        type="button"
        className="cart-item__remove"
        onClick={onRemove}
        aria-label="Удалить"
      >
        ✕
      </button>
    </div>
  )
}
