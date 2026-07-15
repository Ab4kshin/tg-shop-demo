import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"
import type { ReactNode } from "react"
import type { Lang } from "../../shared/types"
import { setAdminLang } from "./api"

export type { Lang }

type Dict = Record<string, string>

const ru: Dict = {
  brand_sub: "админка",
  nav_orders: "Заказы",
  nav_products: "Товары",
  nav_stats: "Аналитика",
  logout: "Выйти",
  loading: "Загрузка…",
  refresh: "Обновить",
  login_title: "Вход в админку",
  login_hint: "Введите пароль администратора",
  password_ph: "Пароль",
  signing_in: "Входим…",
  sign_in: "Войти",
  orders_title: "Заказы",
  col_num: "№",
  col_customer: "Покупатель",
  col_items: "Состав",
  col_method: "Способ",
  col_amount: "Сумма",
  col_status: "Статус",
  no_orders: "Заказов нет.",
  products_title: "Товары",
  col_product: "Товар",
  col_category: "Категория",
  col_price: "Цена",
  active: "Активен",
  hidden: "Скрыт",
  edit: "Изменить",
  hide: "Скрыть",
  show: "Показать",
  form_new: "Новый товар",
  form_edit: "Редактирование #{id}",
  f_title: "Название",
  f_description: "Описание",
  f_price: "Цена",
  f_photo: "Фото (URL)",
  f_category: "Категория",
  f_active: "Активен",
  save: "Сохранить",
  add: "Добавить",
  cancel: "Отмена",
  stats_title: "Аналитика",
  stat_total_orders: "Всего заказов",
  stat_paid: "Оплачено",
  stat_revenue: "Выручка",
  top_products: "Топ товаров",
  th_sold: "Продано",
  th_revenue: "Выручка",
  no_paid: "Пока нет оплаченных заказов.",
  theme_light: "Светлая",
  theme_dark: "Тёмная",
  cat_manage: "Категории",
  cat_new_ph: "Новая категория",
  cat_add: "Добавить",
  cat_delete: "Удалить",
  del: "Удалить",
  del_confirm: "Удалить товар безвозвратно?",
}

const en: Dict = {
  brand_sub: "admin",
  nav_orders: "Orders",
  nav_products: "Products",
  nav_stats: "Analytics",
  logout: "Log out",
  loading: "Loading…",
  refresh: "Refresh",
  login_title: "Admin login",
  login_hint: "Enter the administrator password",
  password_ph: "Password",
  signing_in: "Signing in…",
  sign_in: "Sign in",
  orders_title: "Orders",
  col_num: "#",
  col_customer: "Customer",
  col_items: "Items",
  col_method: "Method",
  col_amount: "Amount",
  col_status: "Status",
  no_orders: "No orders.",
  products_title: "Products",
  col_product: "Product",
  col_category: "Category",
  col_price: "Price",
  active: "Active",
  hidden: "Hidden",
  edit: "Edit",
  hide: "Hide",
  show: "Show",
  form_new: "New product",
  form_edit: "Editing #{id}",
  f_title: "Title",
  f_description: "Description",
  f_price: "Price",
  f_photo: "Photo (URL)",
  f_category: "Category",
  f_active: "Active",
  save: "Save",
  add: "Add",
  cancel: "Cancel",
  stats_title: "Analytics",
  stat_total_orders: "Total orders",
  stat_paid: "Paid",
  stat_revenue: "Revenue",
  top_products: "Top products",
  th_sold: "Sold",
  th_revenue: "Revenue",
  no_paid: "No paid orders yet.",
  theme_light: "Light",
  theme_dark: "Dark",
  cat_manage: "Categories",
  cat_new_ph: "New category",
  cat_add: "Add",
  cat_delete: "Delete",
  del: "Delete",
  del_confirm: "Delete this product permanently?",
}

const messages: Record<Lang, Dict> = { ru, en }

const STATUS: Record<Lang, Record<string, string>> = {
  ru: {
    new: "Ожидает оплаты",
    paid: "Оплачен",
    shipped: "Отправлен",
    done: "Завершён",
    canceled: "Отменён",
  },
  en: {
    new: "Awaiting payment",
    paid: "Paid",
    shipped: "Shipped",
    done: "Done",
    canceled: "Canceled",
  },
}

const METHOD: Record<Lang, Record<string, string>> = {
  ru: {
    mock: "Тестовая",
    robokassa: "Robokassa",
    ton: "TON",
    usdt_ton: "USDT",
    crypto: "Крипта",
    card: "Карта/СБП",
    "": "—",
  },
  en: {
    mock: "Test",
    robokassa: "Robokassa",
    ton: "TON",
    usdt_ton: "USDT",
    crypto: "Crypto",
    card: "Card/SBP",
    "": "—",
  },
}

const CATEGORY: Record<Lang, Record<string, string>> = {
  ru: {
    "День рождения": "День рождения",
    "Свадьба": "Свадьба",
    "Извинение": "Извинение",
    "Без повода": "Без повода",
  },
  en: {
    "День рождения": "Birthday",
    "Свадьба": "Wedding",
    "Извинение": "Apology",
    "Без повода": "Just because",
  },
}

export function statusLabel(lang: Lang, status: string): string {
  return STATUS[lang][status] ?? status
}

export function methodLabel(lang: Lang, method: string): string {
  return METHOD[lang][method] ?? method
}

export function categoryLabel(lang: Lang, category: string): string {
  return CATEGORY[lang][category] ?? category
}

interface I18nValue {
  lang: Lang
  setLang: (l: Lang) => void
  t: (key: string, params?: Record<string, string | number>) => string
}

const I18nContext = createContext<I18nValue | null>(null)
const STORAGE_KEY = "tg-shop-admin-lang"

function detectLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === "ru" || saved === "en") return saved
  } catch {
    /* ignore */
  }
  const nav = (navigator.language || "").toLowerCase()
  return nav.startsWith("ru") ? "ru" : "en"
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      /* ignore */
    }
  }, [lang])

  // Синхронизируем язык админских уведомлений с языком дашборда.
  useEffect(() => {
    setAdminLang(lang)
  }, [lang])

  const setLang = useCallback((l: Lang) => setLangState(l), [])

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      let text = messages[lang][key] ?? messages.en[key] ?? key
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.split("{" + k + "}").join(String(v))
        }
      }
      return text
    },
    [lang],
  )

  const value = useMemo<I18nValue>(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error("useI18n must be used within I18nProvider")
  return ctx
}
