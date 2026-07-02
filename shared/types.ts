// Единый источник общих типов для мини-аппки и админки.
export interface Product {
  id: number
  title: string
  description: string
  price_kopecks: number
  photo_url: string
  category: string
  is_active: boolean
}

export interface OrderItem {
  product_id: number
  title: string
  qty: number
  price_at_purchase_kopecks: number
}
