import type { FormEvent } from "react"
import { categoryLabel, useI18n } from "../i18n"
import type { ProductInput } from "../types"

interface Props {
  editingId: number | null
  form: ProductInput
  categories: string[]
  onChange: (form: ProductInput) => void
  priceValue: string
  currencySymbol: string
  onPriceChange: (value: string) => void
  onSubmit: (e: FormEvent) => void
  onCancel: () => void
}

export function ProductForm({
  editingId,
  form,
  categories,
  onChange,
  priceValue,
  currencySymbol,
  onPriceChange,
  onSubmit,
  onCancel,
}: Props) {
  const { lang, t } = useI18n()
  return (
    <form className="form-card" onSubmit={onSubmit}>
      <h2>
        {editingId ? t("form_edit", { id: editingId }) : t("form_new")}
      </h2>
      <label>
        {t("f_title")}
        <input
          value={form.title}
          onChange={(e) => onChange({ ...form, title: e.target.value })}
          required
        />
      </label>
      <label>
        {t("f_description")}
        <textarea
          value={form.description}
          onChange={(e) => onChange({ ...form, description: e.target.value })}
          rows={3}
        />
      </label>
      <label>
        {t("f_price")}, {currencySymbol}
        <input
          type="number"
          min="0"
          step="0.01"
          value={priceValue}
          onChange={(e) => onPriceChange(e.target.value)}
          required
        />
      </label>
      <label>
        {t("f_photo")}
        <input
          value={form.photo_url}
          onChange={(e) => onChange({ ...form, photo_url: e.target.value })}
        />
      </label>
      <label>
        {t("f_category")}
        <select
          value={form.category}
          onChange={(e) => onChange({ ...form, category: e.target.value })}
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {categoryLabel(lang, c)}
            </option>
          ))}
        </select>
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(e) => onChange({ ...form, is_active: e.target.checked })}
        />
        {t("f_active")}
      </label>
      <div className="form-actions">
        <button type="submit" className="btn btn--primary">
          {editingId ? t("save") : t("add")}
        </button>
        {editingId && (
          <button type="button" className="btn" onClick={onCancel}>
            {t("cancel")}
          </button>
        )}
      </div>
    </form>
  )
}
