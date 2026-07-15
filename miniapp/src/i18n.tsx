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
import { getLanguageCode } from "./telegram"

export type { Lang }

type Dict = Record<string, string>

const MESSAGES: Record<string, [string, string]> = {
  tab_catalog: ["Каталог", "Catalog"],
  tab_cart: ["Корзина", "Cart"],
  tab_orders: ["Заказы", "Orders"],
  shop_title: ["Магазин подарков", "Gift Shop"],
  loading: ["Загрузка…", "Loading…"],
  nothing_found: ["Ничего не найдено.", "Nothing found."],
  category_all: ["Все", "All"],
  add_to_cart: ["В корзину", "Add to cart"],
  cart_title: ["Корзина", "Cart"],
  cart_empty: ["Корзина пуста.", "Your cart is empty."],
  go_to_catalog: ["Перейти в каталог", "Go to catalog"],
  total: ["Итого", "Total"],
  creating_order: ["Создаём заказ…", "Creating order…"],
  checkout: ["Оформить и оплатить", "Checkout & pay"],
  methods_none: ["Способы оплаты пока не настроены.", "No payment methods configured yet."],
  payment_method: ["Способ оплаты", "Payment method"],
  remove: ["Удалить", "Remove"],
  my_orders: ["Мои заказы", "My orders"],
  no_orders: ["Заказов пока нет.", "No orders yet."],
  order_no: ["Заказ №{id}", "Order #{id}"],
  pay_in: ["Оплата в {asset}", "Pay in {asset}"],
  wallet: ["Кошелёк", "Wallet"],
  comment_hint: ["Комментарий к переводу ({comment}) подставляется автоматически — не меняйте его, по нему подтверждается оплата.", "The transfer comment ({comment}) is added automatically — don't change it, the payment is confirmed by it."],
  network_testnet: ["Сеть: testnet (тестовые монеты).", "Network: testnet (test coins)."],
  connect_wallet_first: ["Сначала подключите кошелёк", "Connect your wallet first"],
  sending: ["Отправляем…", "Sending…"],
  pay_button: ["Оплатить {amount} {asset}", "Pay {amount} {asset}"],
  after_confirm_hint: ["После подтверждения в кошельке оплата определится автоматически за несколько секунд.", "After you confirm in your wallet, the payment is detected automatically within seconds."],
  paid_title: ["Оплачено ✅", "Paid ✅"],
  paid_desc: ["Заказ №{id} оплачен в {asset}. Бот прислал подтверждение.", "Order #{id} paid in {asset}. The bot sent a confirmation."],
  to_my_orders: ["К моим заказам", "To my orders"],
  err_send: ["Не удалось отправить транзакцию", "Failed to send the transaction"],
  err_no_usdt_wallet: ["У кошелька нет USDT-баланса в сети TON", "This wallet has no USDT balance in the TON network"],
  err_find_usdt_wallet: ["Не удалось найти ваш USDT-кошелёк в сети TON", "Couldn't find your USDT wallet in the TON network"],
  err_bad_usdt_addr: ["Получен некорректный адрес USDT-кошелька от TonAPI", "Received an invalid USDT wallet address from TonAPI"],
  to_pay: ["К оплате:", "To pay:"],
  copy_details: ["📋 Скопировать реквизиты", "📋 Copy details"],
  copied: ["Скопировано ✓", "Copied ✓"],
  claimed_note: ["✅ Спасибо! Мы проверим поступление и подтвердим заказ. Статус — в разделе «Заказы».", "✅ Thanks! We'll verify the payment and confirm your order. The status is in the “Orders” tab."],
  i_paid: ["Я оплатил", "I've paid"],
}

// ru/en выводятся из единой таблицы MESSAGES — без дублирующихся словарей.
const ru: Dict = {}
const en: Dict = {}
for (const [key, [rus, eng]] of Object.entries(MESSAGES)) {
  ru[key] = rus
  en[key] = eng
}

const messages: Record<Lang, Dict> = { ru, en }

// Категории хранятся в БД по-русски; это их отображаемые подписи.
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

// Подписи способов оплаты по id (backend отдаёт русские title/description).
// Для EN подменяем их по id; для неизвестных id — фоллбэк на бэкенд.
export const METHOD_LABELS: Record<
  Lang,
  Record<string, { title: string; description: string }>
> = {
  ru: {},
  en: {
    mock: {
      title: "Test payment",
      description: "Instant test payment (no real charge)",
    },
    robokassa: {
      title: "Bank card (Robokassa)",
      description: "Pay by card via Robokassa",
    },
    ton: { title: "TON", description: "Pay with TON via TON Connect" },
    usdt_ton: {
      title: "USDT (TON)",
      description: "Pay with USDT in the TON network",
    },
    manual: {
      title: "Manual transfer",
      description: "Transfer by the details, then tap “I've paid”",
    },
  },
}

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

export function statusLabel(lang: Lang, status: string): string {
  return STATUS[lang][status] ?? status
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
const STORAGE_KEY = "tg-shop-lang"

// Единая точка сохранения выбранного языка (используется и при детекте, и в эффекте).
function saveLang(lang: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    /* ignore */
  }
}

// Язык из URL (?lang=ru|en) — его пробрасывает бот после выбора языка в /start.
function urlLang(): Lang | null {
  try {
    const v = (new URLSearchParams(window.location.search).get("lang") || "")
      .toLowerCase()
    if (v === "ru" || v === "en") return v
  } catch {
    /* ignore */
  }
  return null
}

function detectLang(): Lang {
  // 1) Явный выбор из бота (URL) — высший приоритет, сразу запоминаем.
  const fromUrl = urlLang()
  if (fromUrl) {
    saveLang(fromUrl)
    return fromUrl
  }
  // 2) Сохранённый ранее выбор.
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === "ru" || saved === "en") return saved
  } catch {
    /* ignore */
  }
  // 3) Язык Telegram.
  const code = (getLanguageCode() || "").toLowerCase()
  return code.startsWith("ru") ? "ru" : "en"
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang)

  useEffect(() => {
    saveLang(lang)
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

  const value = useMemo<I18nValue>(
    () => ({ lang, setLang, t }),
    [lang, setLang, t],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error("useI18n должен быть внутри I18nProvider")
  return ctx
}
