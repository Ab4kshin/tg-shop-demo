export function formatPrice(kopecks: number): string {
  const rub = kopecks / 100
  return (
    rub.toLocaleString("ru-RU", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }) + "\u00a0₽"
  )
}
