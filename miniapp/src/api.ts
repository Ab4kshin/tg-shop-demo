import { getInitData } from "./telegram"
import type {
  CreateOrderResult,
  Currency,
  Order,
  PaymentMethod,
  Product,
} from "./types"

const API_URL = (import.meta.env.VITE_API_URL as string) || ""

function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `tma ${getInitData()}`,
    // Пропускаем страницу-предупреждение бесплатного ngrok
    "ngrok-skip-browser-warning": "true",
  }
}

async function handle<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail: string = resp.statusText
    try {
      const data = await resp.json()
      if (typeof data.detail === "string") detail = data.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail || "Ошибка запроса")
  }
  return (await resp.json()) as T
}

export async function fetchProducts(category?: string): Promise<Product[]> {
  const query = category ? `?category=${encodeURIComponent(category)}` : ""
  const resp = await fetch(`${API_URL}/api/products${query}`, {
    headers: headers(),
  })
  return handle<Product[]>(resp)
}

export async function fetchCategories(): Promise<string[]> {
  const resp = await fetch(`${API_URL}/api/categories`, { headers: headers() })
  return handle<string[]>(resp)
}

export async function fetchCurrencies(): Promise<Currency[]> {
  const resp = await fetch(`${API_URL}/api/currencies`, { headers: headers() })
  const data = await handle<{ base: string; currencies: Currency[] }>(resp)
  return data.currencies
}

export async function fetchPaymentMethods(): Promise<PaymentMethod[]> {
  const resp = await fetch(`${API_URL}/api/payment-methods`, {
    headers: headers(),
  })
  return handle<PaymentMethod[]>(resp)
}

export async function createOrder(
  items: { product_id: number; qty: number }[],
  method: string,
  note = "",
): Promise<CreateOrderResult> {
  const resp = await fetch(`${API_URL}/api/orders`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ items, method, note }),
  })
  return handle<CreateOrderResult>(resp)
}

export async function claimPaid(orderId: number): Promise<void> {
  await handle(
    await fetch(`${API_URL}/api/orders/${orderId}/claim`, {
      method: "POST",
      headers: headers(),
    }),
  )
}

export async function checkTonPayment(
  orderId: number,
): Promise<{ status: string }> {
  const resp = await fetch(`${API_URL}/api/ton/check/${orderId}`, {
    headers: headers(),
  })
  return handle<{ status: string }>(resp)
}

export async function fetchMyOrders(): Promise<Order[]> {
  const resp = await fetch(`${API_URL}/api/orders`, { headers: headers() })
  return handle<Order[]>(resp)
}
