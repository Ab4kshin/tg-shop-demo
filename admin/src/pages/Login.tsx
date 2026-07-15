import { useState } from "react"
import type { FormEvent } from "react"
import { login, setToken } from "../api"
import { useI18n } from "../i18n"

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const { t } = useI18n()
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
        <h1>{t("login_title")}</h1>
        <p className="muted">{t("login_hint")}</p>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={t("password_ph")}
          autoFocus
        />
        {error && <div className="error">{error}</div>}
        <button className="btn btn--primary" disabled={loading || !password}>
          {loading ? t("signing_in") : t("sign_in")}
        </button>
      </form>
    </div>
  )
}
