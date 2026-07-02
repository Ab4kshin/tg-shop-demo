export function formatPrice(kopecks: number): string {
  const rub = kopecks / 100
  return (
    rub.toLocaleString("ru-RU", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }) + "\u00a0₽"
  )
}

export const STATUS_LABELS: Record<string, string> = {
  new: "Ожидает оплаты",
  paid: "Оплачен",
  shipped: "Отправлен",
  done: "Завершён",
  canceled: "Отменён",
}
