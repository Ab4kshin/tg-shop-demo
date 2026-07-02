import type { OrderItem, Product } from "../../shared/types"

export type { OrderItem, Product }

export const CATEGORIES = [
  "День рождения",
  "Свадьба",
  "Извинение",
  "Без повода",
] as const

export interface Order {
  id: number
  status: string
  total_kopecks: number
  note: string
  created_at: string
  items: OrderItem[]
}

export interface PaymentMethod {
  id: string
  title: string
  description: string
}

export interface ManualInstructions {
  method: string
  title: string
  details: string
  amount_kopecks: number
  qr_svg: string
}

export interface CreateOrderResult {
  order_id: number
  kind: string
  confirmation_url?: string | null
  instructions?: ManualInstructions | null
}
