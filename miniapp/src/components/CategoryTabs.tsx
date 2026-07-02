import { CATEGORIES } from "../types"

interface Props {
  active: string | null
  onChange: (category: string | null) => void
}

export function CategoryTabs({ active, onChange }: Props) {
  return (
    <div className="chips">
      <button
        type="button"
        className={`chip ${active === null ? "chip--active" : ""}`}
        onClick={() => onChange(null)}
      >
        Все
      </button>
      {CATEGORIES.map((category) => (
        <button
          key={category}
          type="button"
          className={`chip ${active === category ? "chip--active" : ""}`}
          onClick={() => onChange(category)}
        >
          {category}
        </button>
      ))}
    </div>
  )
}
