import { useCurrency } from "../currency"
import { categoryLabel, useI18n } from "../i18n"
import type { Product } from "../types"

interface Props {
  products: Product[]
  onEdit: (product: Product) => void
  onToggle: (product: Product) => void
  onDelete: (product: Product) => void
}

export function ProductsTable({
  products,
  onEdit,
  onToggle,
  onDelete,
}: Props) {
  const { lang, t } = useI18n()
  const { format } = useCurrency()
  return (
    <table className="table">
      <thead>
        <tr>
          <th>{t("col_product")}</th>
          <th>{t("col_category")}</th>
          <th>{t("col_price")}</th>
          <th>{t("col_status")}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {products.map((product) => (
          <tr key={product.id} className={product.is_active ? "" : "row-muted"}>
            <td>{product.title}</td>
            <td>{categoryLabel(lang, product.category)}</td>
            <td>{format(product.price_kopecks)}</td>
            <td>{product.is_active ? t("active") : t("hidden")}</td>
            <td className="row-actions">
              <button className="btn btn--sm" onClick={() => onEdit(product)}>
                {t("edit")}
              </button>
              <button className="btn btn--sm" onClick={() => onToggle(product)}>
                {product.is_active ? t("hide") : t("show")}
              </button>
              <button
                className="btn btn--sm btn--danger"
                onClick={() => onDelete(product)}
              >
                {t("del")}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
