import type { Product } from "../types"
import { formatPrice } from "../utils"

interface Props {
  products: Product[]
  onEdit: (product: Product) => void
  onToggle: (product: Product) => void
}

export function ProductsTable({ products, onEdit, onToggle }: Props) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Товар</th>
          <th>Категория</th>
          <th>Цена</th>
          <th>Статус</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {products.map((product) => (
          <tr key={product.id} className={product.is_active ? "" : "row-muted"}>
            <td>{product.title}</td>
            <td>{product.category}</td>
            <td>{formatPrice(product.price_kopecks)}</td>
            <td>{product.is_active ? "Активен" : "Скрыт"}</td>
            <td className="row-actions">
              <button className="btn btn--sm" onClick={() => onEdit(product)}>
                Изменить
              </button>
              <button className="btn btn--sm" onClick={() => onToggle(product)}>
                {product.is_active ? "Скрыть" : "Показать"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
