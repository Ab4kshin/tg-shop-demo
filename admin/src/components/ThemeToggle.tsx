import { useI18n } from "../i18n"
import { useTheme } from "../theme"

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const { t } = useI18n()
  return (
    <button type="button" className="theme-toggle" onClick={toggle}>
      {theme === "dark" ? `\u2600\ufe0f ${t("theme_light")}` : `\ud83c\udf19 ${t("theme_dark")}`}
    </button>
  )
}
