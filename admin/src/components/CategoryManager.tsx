import { useState } from "react"
import type { FormEvent } from "react"
import { categoryLabel, useI18n } from "../i18n"

interface Props {
  categories: string[]
  onAdd: (name: string) => Promise<void>
  onDelete: (name: string) => Promise<void>
}

export function CategoryManager({ categories, onAdd, onDelete }: Props) {
  const { lang, t } = useI18n()
  const [newCategory, setNewCategory] = useState("")

  async function submit(e: FormEvent) {
    e.preventDefault()
    const name = newCategory.trim()
    if (!name) return
    await onAdd(name)
    setNewCategory("")
  }

  return (
    <div className="cat-manager">
      <h3>{t("cat_manage")}</h3>
      <form className="cat-manager__add" onSubmit={submit}>
        <input
          value={newCategory}
          placeholder={t("cat_new_ph")}
          onChange={(e) => setNewCategory(e.target.value)}
        />
        <button type="submit" className="btn btn--sm">
          {t("cat_add")}
        </button>
      </form>
      <div className="cat-list">
        {categories.map((c) => (
          <div className="cat-list__row" key={c}>
            <span>{categoryLabel(lang, c)}</span>
            <button
              type="button"
              className="btn btn--sm"
              onClick={() => onDelete(c)}
            >
              {t("cat_delete")}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
