import type { AdminOrder, Currency, Product, ProductInput, Stats } from "./types"

const API_URL = (import.meta.env.VITE_API_URL as string) || ""
const TOKEN_KEY = "tg-shop-admin-token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

function headers(): HeadersInit {
  const result: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
  }
  const token = getToken()
  if (token) result["X-Admin-Token"] = token
  return result
}

async function handle<T>(resp: Response): Promise<T> {
  if (resp.status === 401) {
    clearToken()
    throw new Error("Требуется вход")
  }
  if (!resp.ok) {
    let detail: string = resp.statusText
    try {
      const data = await resp.json()
      if (typeof data.detail === "string") detail = data.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail || "Ошибка")
  }
  return (await resp.json()) as T
}

export async function login(password: string): Promise<string> {
  const resp = await fetch(`${API_URL}/api/admin/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    },
    body: JSON.stringify({ password }),
  })
  const data = await handle<{ token: string }>(resp)
  return data.token
}

export async function fetchOrders(): Promise<AdminOrder[]> {
  return handle<AdminOrder[]>(
    await fetch(`${API_URL}/api/admin/orders`, { headers: headers() }),
  )
}

export async function updateOrderStatus(
  id: number,
  status: string,
): Promise<void> {
  await handle(
    await fetch(`${API_URL}/api/admin/orders/${id}`, {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify({ status }),
    }),
  )
}

export async function fetchProducts(): Promise<Product[]> {
  return handle<Product[]>(
    await fetch(`${API_URL}/api/admin/products`, { headers: headers() }),
  )
}

export async function createProduct(product: ProductInput): Promise<Product> {
  return handle<Product>(
    await fetch(`${API_URL}/api/admin/products`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(product),
    }),
  )
}

export async function updateProduct(
  id: number,
  product: Partial<ProductInput>,
): Promise<Product> {
  return handle<Product>(
    await fetch(`${API_URL}/api/admin/products/${id}`, {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify(product),
    }),
  )
}

export async function fetchStats(): Promise<Stats> {
  return handle<Stats>(
    await fetch(`${API_URL}/api/admin/stats`, { headers: headers() }),
  )
}

export async function fetchCategories(): Promise<string[]> {
  return handle<string[]>(
    await fetch(`${API_URL}/api/categories`, { headers: headers() }),
  )
}

export async function fetchCurrencies(): Promise<Currency[]> {
  const data = await handle<{ base: string; currencies: Currency[] }>(
    await fetch(`${API_URL}/api/currencies`, { headers: headers() }),
  )
  return data.currencies
}

export async function createCategory(name: string): Promise<void> {
  await handle(
    await fetch(`${API_URL}/api/admin/categories`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ name }),
    }),
  )
}

export async function deleteCategory(name: string): Promise<void> {
  await handle(
    await fetch(
      `${API_URL}/api/admin/categories/${encodeURIComponent(name)}`,
      { method: "DELETE", headers: headers() },
    ),
  )
}

export async function deleteProduct(id: number): Promise<void> {
  await handle(
    await fetch(`${API_URL}/api/admin/products/${id}`, {
      method: "DELETE",
      headers: headers(),
    }),
  )
}

// Персистим язык админских уведомлений. Best-effort: ошибки глотаем,
// токен не трогаем (чтобы не выкидывать админа при 401).
export function setAdminLang(lang: string): void {
  if (!getToken()) return
  void fetch(`${API_URL}/api/admin/admin-lang`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ lang }),
  }).catch(() => {
    /* ignore */
  })
}
