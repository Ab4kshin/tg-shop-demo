import { useState } from "react"
import type { FormEvent } from "react"
import { login, setToken } from "../api"

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const token = await login(password)
      setToken(token)
      onSuccess()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login">
      <form className="login__card" onSubmit={submit}>
        <h1>Вход в админку</h1>
        <p className="muted">Введите пароль администратора</p>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Пароль"
          autoFocus
        />
        {error && <div className="error">{error}</div>}
        <button className="btn btn--primary" disabled={loading || !password}>
          {loading ? "Входим…" : "Войти"}
        </button>
      </form>
    </div>
  )
}
