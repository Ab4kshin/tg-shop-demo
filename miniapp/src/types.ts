import type { Currency, OrderItem, Product } from "../../shared/types"

export type { Currency, OrderItem, Product }

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

export interface TonPayment {
  order_id: number
  address: string
  amount_nano: string
  amount_ton: string
  amount_rub: number
  comment: string
  network: string
  manifest_url: string
  expires_at: number
  // "ton" (нативная монета) или "usdt" (жетон jUSDT)
  asset: string
  asset_label: string
  jetton_master: string
  amount_units: string
  usdt_decimals: number
}

export interface CreateOrderResult {
  order_id: number
  kind: string
  confirmation_url?: string | null
  instructions?: ManualInstructions | null
  ton?: TonPayment | null
}
