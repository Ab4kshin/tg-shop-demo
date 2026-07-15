import { Address, beginCell, toNano } from "@ton/core"
import {
  THEME,
  TonConnectButton,
  useTonConnectUI,
  useTonWallet,
} from "@tonconnect/ui-react"
import { useEffect, useRef, useState } from "react"
import { checkTonPayment } from "../api"
import { useCurrency } from "../currency"
import { useI18n } from "../i18n"
import { tg } from "../telegram"
import type { TonPayment } from "../types"

interface Props {
  payment: TonPayment
  onPaid: () => void
  onDone: () => void
}

// Тело простого текстового комментария (op = 0).
function commentPayload(text: string): string {
  return beginCell()
    .storeUint(0, 32)
    .storeStringTail(text)
    .endCell()
    .toBoc()
    .toString("base64")
}

function tonapiBase(network: string): string {
  return network === "testnet"
    ? "https://testnet.tonapi.io"
    : "https://tonapi.io"
}

// Адрес jetton-кошелька отправителя — именно ему шлём transfer-сообщение.
async function resolveJettonWallet(
  t: (k: string) => string,
  network: string,
  owner: string,
  master: string,
): Promise<string> {
  const resp = await fetch(
    `${tonapiBase(network)}/v2/accounts/${owner}/jettons/${master}`,
  )
  if (!resp.ok) throw new Error(t("err_find_usdt_wallet"))
  const data = await resp.json()
  const addr = data?.wallet_address?.address
  if (!addr) throw new Error(t("err_no_usdt_wallet"))
  // TonAPI отдаёт адрес в raw-формате (0:...). TON Connect такой формат
  // отклоняет («Wrong 'address' format»), поэтому нормализуем в дружелюбный.
  try {
    return Address.parse(addr as string).toString()
  } catch {
    throw new Error(t("err_bad_usdt_addr"))
  }
}

// Тело jetton transfer (TEP-74): op 0x0f8a7ea5 + сумма + получатель + комментарий.
function jettonTransferPayload(
  amountUnits: string,
  destination: string,
  responseTo: string,
  comment: string,
): string {
  const forward = beginCell()
    .storeUint(0, 32)
    .storeStringTail(comment)
    .endCell()
  return beginCell()
    .storeUint(0x0f8a7ea5, 32)
    .storeUint(0, 64)
    .storeCoins(BigInt(amountUnits))
    .storeAddress(Address.parse(destination))
    .storeAddress(Address.parse(responseTo))
    .storeBit(false)
    .storeCoins(toNano("0.02"))
    .storeBit(true)
    .storeRef(forward)
    .endCell()
    .toBoc()
    .toString("base64")
}

export function TonPaymentPanel({ payment, onPaid, onDone }: Props) {
  const { lang, t } = useI18n()
  const { format } = useCurrency()
  const [tonConnectUI] = useTonConnectUI()
  const wallet = useTonWallet()
  const [sending, setSending] = useState(false)
  const [paid, setPaid] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)
  const asset = payment.asset_label || "TON"
  const [scheme, setScheme] = useState<"light" | "dark">(
    () => tg()?.colorScheme ?? "light",
  )

  function stopPolling() {
    if (pollRef.current != null) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  function startPolling() {
    stopPolling()
    pollRef.current = window.setInterval(async () => {
      try {
        const res = await checkTonPayment(payment.order_id)
        if (res.status === "paid") {
          stopPolling()
          setPaid(true)
          onPaid()
        }
      } catch {
        /* временная ошибка сети — продолжаем опрос */
      }
    }, 3500)
  }

  useEffect(() => stopPolling, [])

  // Следим за темой Telegram (тёмная/светлая), чтобы виджет TON Connect
  // не оставался белым при тёмной теме.
  useEffect(() => {
    const app = tg()
    if (!app) return
    const update = () => setScheme(app.colorScheme || "light")
    update()
    app.onEvent("themeChanged", update)
  }, [])

  // Язык и тему виджета TON Connect (вкл. тост «транзакция отправлена»)
  // синхронизируем реактивно: пропы language/тема на провайдере применяются
  // только при монтировании и не меняются при переключении.
  useEffect(() => {
    tonConnectUI.uiOptions = {
      language: lang === "en" ? "en" : "ru",
      uiPreferences: { theme: scheme === "dark" ? THEME.DARK : THEME.LIGHT },
    }
  }, [tonConnectUI, lang, scheme])

  async function pay() {
    setError(null)
    setSending(true)
    try {
      if (payment.asset === "usdt") {
        const owner = wallet?.account?.address
        if (!owner) throw new Error(t("connect_wallet_first"))
        const jettonWallet = await resolveJettonWallet(
          t,
          payment.network,
          owner,
          payment.jetton_master || "",
        )
        await tonConnectUI.sendTransaction({
          validUntil: Math.floor(Date.now() / 1000) + 360,
          messages: [
            {
              address: jettonWallet,
              amount: toNano("0.1").toString(),
              payload: jettonTransferPayload(
                payment.amount_units || "0",
                payment.address,
                owner,
                payment.comment,
              ),
            },
          ],
        })
      } else {
        await tonConnectUI.sendTransaction({
          validUntil: Math.floor(Date.now() / 1000) + 360,
          messages: [
            {
              address: payment.address,
              amount: payment.amount_nano,
              payload: commentPayload(payment.comment),
            },
          ],
        })
      }
      startPolling()
    } catch (e) {
      setError((e as Error).message || t("err_send"))
    } finally {
      setSending(false)
    }
  }

  if (paid) {
    return (
      <div className="page">
        <h1 className="page__title">{t("paid_title")}</h1>
        <p className="hint">{t("paid_desc", { id: payment.order_id, asset })}</p>
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={onDone}
        >
          {t("to_my_orders")}
        </button>
      </div>
    )
  }

  return (
    <div className="page">
      <h1 className="page__title">{t("pay_in", { asset })}</h1>
      <div className="pay-amount">
        {payment.amount_ton} {asset}
        <span className="hint">
          {" ≈ "}
          {format(Math.round(payment.amount_rub * 100))}
        </span>
      </div>

      <div className="methods__title">{t("wallet")}</div>
      <TonConnectButton />

      <p className="hint">{t("comment_hint", { comment: payment.comment })}</p>
      {payment.network === "testnet" && (
        <p className="hint">{t("network_testnet")}</p>
      )}

      {error && <p className="error">{error}</p>}

      <button
        type="button"
        className="btn btn--primary btn--block"
        disabled={sending || !wallet}
        onClick={pay}
      >
        {!wallet
          ? t("connect_wallet_first")
          : sending
            ? t("sending")
            : t("pay_button", { amount: payment.amount_ton, asset })}
      </button>

      <p className="hint">{t("after_confirm_hint")}</p>
    </div>
  )
}
