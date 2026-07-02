import type { FormEvent } from "react"
import { CATEGORIES } from "../types"
import type { ProductInput } from "../types"

interface Props {
  editingId: number | null
  form: ProductInput
  onChange: (form: ProductInput) => void
  priceRub: string
  onPriceRubChange: (value: string) => void
  onSubmit: (e: FormEvent) => void
  onCancel: () => void
}

export function ProductForm({
  editingId,
  form,
  onChange,
  priceRub,
  onPriceRubChange,
  onSubmit,
  onCancel,
}: Props) {
  return (
    <form className="form-card" onSubmit={onSubmit}>
      <h2>{editingId ? `Редактирование #${editingId}` : "Новый товар"}</h2>
      <label>
        Название
        <input
          value={form.title}
          onChange={(e) => onChange({ ...form, title: e.target.value })}
          required
        />
      </label>
      <label>
        Описание
        <textarea
          value={form.description}
          onChange={(e) => onChange({ ...form, description: e.target.value })}
          rows={3}
        />
      </label>
      <label>
        Цена, ₽
        <input
          type="number"
          min="0"
          step="0.01"
          value={priceRub}
          onChange={(e) => onPriceRubChange(e.target.value)}
          required
        />
      </label>
      <label>
        Фото (URL)
        <input
          value={form.photo_url}
          onChange={(e) => onChange({ ...form, photo_url: e.target.value })}
        />
      </label>
      <label>
        Категория
        <select
          value={form.category}
          onChange={(e) => onChange({ ...form, category: e.target.value })}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
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
        Активен
      </label>
      <div className="form-actions">
        <button type="submit" className="btn btn--primary">
          {editingId ? "Сохранить" : "Добавить"}
        </button>
        {editingId && (
          <button type="button" className="btn" onClick={onCancel}>
            Отмена
          </button>
        )}
      </div>
    </form>
  )
}
