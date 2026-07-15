import { categoryLabel, useI18n } from "../i18n"

interface Props {
  categories: string[]
  active: string | null
  onChange: (category: string | null) => void
}

export function CategoryTabs({ categories, active, onChange }: Props) {
  const { lang, t } = useI18n()
  return (
    <div className="chips">
      <button
        type="button"
        className={`chip ${active === null ? "chip--active" : ""}`}
        onClick={() => onChange(null)}
      >
        {t("category_all")}
      </button>
      {categories.map((category) => (
        <button
          key={category}
          type="button"
          className={`chip ${active === category ? "chip--active" : ""}`}
          onClick={() => onChange(category)}
        >
          {categoryLabel(lang, category)}
        </button>
      ))}
    </div>
  )
}
