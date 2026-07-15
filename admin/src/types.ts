import type { Currency, OrderItem, Product } from "../../shared/types"

export type { Currency, OrderItem, Product }

export const CATEGORIES = [
  "День рождения",
  "Свадьба",
  "Извинение",
  "Без повода",
] as const

export const STATUSES = ["new", "paid", "shipped", "done", "canceled"] as const

export interface ProductInput {
  title: string
  description: string
  price_kopecks: number
  photo_url: string
  category: string
  is_active: boolean
}

export interface AdminOrder {
  id: number
  status: string
  total_kopecks: number
  note: string
  created_at: string
  updated_at: string
  user_tg_id: number
  user_name: string
  payment_id: string | null
  payment_method: string
  items: OrderItem[]
}

export interface TopProduct {
  id: number
  title: string
  qty: number
  revenue_kopecks: number
}

export interface Stats {
  total_orders: number
  paid_orders: number
  revenue_kopecks: number
  top_products: TopProduct[]
}
