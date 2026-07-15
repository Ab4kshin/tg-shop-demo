#!/usr/bin/env bash
# TG Shop — единый скрипт управления проектом (SINGLE-ORIGIN).
#
# Идея как в moneyflow: бэкенд сам отдаёт собранную мини-аппку, поэтому нужен
# ОДИН туннель ngrok, а его адрес автоматически становится адресом мини-аппки.
# Скрипт сам заполняет .env, прописывает манифест TON Connect и ставит кнопку
# меню в Telegram через Bot API. Секреты живут только в .env.
#
# ПОРЯДОК (без «курицы и яйца»):
#   1) ./tgshop.sh setup    — один раз: зависимости + БД
#   2) ./tgshop.sh config   — токен, ID, пароль, оплата (адрес ngrok НЕ нужен)
#   3) ./tgshop.sh dev      — ОКНО 1: backend (отдаёт API + мини-аппку) + bot
#   4) ./tgshop.sh ngrok    — ОКНО 2: туннель, держать открытым
#   5) ./tgshop.sh build    — ОКНО 3: соберёт мини-аппку, сам пропишет адрес,
#                             манифест TON и кнопку меню в Telegram
#   6) открой бота → кнопка «🛍️ Магазин» или команда /start
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PORT=8000
HEALTH_URL="http://127.0.0.1:${PORT}/health"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
BACKEND_ENV="backend/.env"
BOT_ENV="bot/.env"

c_blue='\033[1;34m'; c_grn='\033[1;32m'; c_yel='\033[1;33m'; c_red='\033[1;31m'; c_off='\033[0m'
say()  { echo -e "${c_blue}▸${c_off} $*"; }
ok()   { echo -e "${c_grn}✔${c_off} $*"; }
warn() { echo -e "${c_yel}⚠${c_off} $*"; }
die()  { echo -e "${c_red}✖${c_off} $*" >&2; exit 1; }

# ---------- вспомогательные ----------
ask() {  # ask VAR "Вопрос" "значение-по-умолчанию"  (Enter — оставить дефолт)
  local __var="$1" __p="$2" __d="${3:-}" __in
  if [ -n "$__d" ]; then
    read -r -p "$__p [$__d]: " __in
    __in="${__in:-$__d}"
  else
    read -r -p "$__p: " __in
  fi
  printf -v "$__var" '%s' "$__in"
}

gen_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 -c 'import secrets; print(secrets.token_hex(32))'
  fi
}

read_env() {  # read_env <file> <KEY> -> печатает значение
  local f="$1" k="$2"
  [ -f "$f" ] || return 0
  grep -E "^${k}=" "$f" | tail -n1 | cut -d= -f2-
}

set_env() {  # set_env <file> <KEY> <value> : upsert KEY=value (не трогает остальное)
  local f="$1" k="$2" v="$3"
  touch "$f"
  python3 - "$f" "$k" "$v" <<'PY'
import re, sys, os
f, k, v = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(f, encoding="utf-8").read() if os.path.exists(f) else ""
if re.search(rf"(?m)^{re.escape(k)}=.*$", text):
    text = re.sub(rf"(?m)^{re.escape(k)}=.*$", lambda m: f"{k}={v}", text)
else:
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"{k}={v}\n"
open(f, "w", encoding="utf-8").write(text)
PY
}

ensure_env() {
  [ -f "$BACKEND_ENV" ] || { cp .env.example "$BACKEND_ENV" 2>/dev/null && ok "создан $BACKEND_ENV из .env.example"; }
  [ -f "$BOT_ENV" ]     || { cp bot/.env.example "$BOT_ENV" 2>/dev/null || touch "$BOT_ENV"; }
}

detect_ngrok_url() {  # печатает первый https-туннель ngrok, либо пусто
  curl -s "$NGROK_API" 2>/dev/null | python3 -c 'import sys, json
try:
    d = json.load(sys.stdin)
    print(next((t["public_url"] for t in d.get("tunnels", []) if t.get("public_url", "").startswith("https")), ""))
except Exception:
    print("")' 2>/dev/null || true
}

sync_bot_env() {  # копирует нужные ключи из backend/.env в bot/.env
  ensure_env
  set_env "$BOT_ENV" BOT_TOKEN       "$(read_env "$BACKEND_ENV" BOT_TOKEN)"
  set_env "$BOT_ENV" MINIAPP_URL     "$(read_env "$BACKEND_ENV" MINIAPP_URL)"
  set_env "$BOT_ENV" BOT_API_URL     "$(read_env "$BACKEND_ENV" BOT_API_URL)"
  set_env "$BOT_ENV" INTERNAL_SECRET "$(read_env "$BACKEND_ENV" INTERNAL_SECRET)"
}

set_menu_button() {  # ставит кнопку меню Telegram на адрес мини-аппки
  local url="$1" token payload api
  token="$(read_env "$BACKEND_ENV" BOT_TOKEN)"
  [ -n "$token" ] || { warn "BOT_TOKEN не задан — пропускаю кнопку меню."; return 0; }
  [ -n "$url" ]   || return 0
  say "Прописываю кнопку меню в Telegram (Bot API)…"
  payload="{\"menu_button\":{\"type\":\"web_app\",\"text\":\"🛍️ Магазин\",\"web_app\":{\"url\":\"$url\"}}}"
  api="https://api.telegram.org/bot${token}/setChatMenuButton"
  if curl -sf "$api" -H 'Content-Type: application/json' -d "$payload" >/dev/null 2>&1; then
    ok "Кнопка меню теперь открывает мини-аппку"
  else
    warn "Не удалось поставить кнопку меню автоматически (проверь токен/сеть)."
  fi
}

write_ton_manifest() {  # write_ton_manifest <base-url>
  local base="${1%/}"
  mkdir -p miniapp/public
  cat > miniapp/public/tonconnect-manifest.json <<EOF
{
  "url": "$base",
  "name": "TG Shop",
  "iconUrl": "https://ton.org/download/ton_symbol.png"
}
EOF
}

print_order() {
  cat <<'MSG'
ПОРЯДОК ЗАПУСКА (тест с телефона, single-origin — ОДИН туннель):

  1) ./tgshop.sh setup     — один раз: зависимости + БД
  2) ./tgshop.sh config    — токен, ID, пароль, оплата (адрес ngrok НЕ нужен!)
  3) ./tgshop.sh dev       — ОКНО 1: backend (API + мини-аппка) + bot, держать
  4) ./tgshop.sh ngrok     — ОКНО 2: туннель, держать открытым
  5) ./tgshop.sh build     — ОКНО 3: соберёт мини-аппку, сам возьмёт ngrok-адрес,
                             пропишет MINIAPP_URL/манифест TON и кнопку меню
  6) открой бота → кнопка «🛍️ Магазин» или /start

Админка (товары/цены/заказы): адрес ngrok + /admin, пароль = ADMIN_PASSWORD из config.
Netlify больше НЕ обязателен: мини-аппку отдаёт сам бэкенд по адресу ngrok.
Способы оплаты можно донастроить: ./tgshop.sh pay | robokassa | ton
Ключ: СНАЧАЛА dev → ПОТОМ ngrok → ПОТОМ build. Окна dev и ngrok не закрывать.
MSG
}

# ---------- команды ----------
do_setup() {
  say "Python venv + зависимости (backend + bot)"
  [ -d .venv ] || python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip >/dev/null
  pip install -r backend/requirements.txt -r bot/requirements.txt
  ensure_env
  [ -n "$(read_env "$BACKEND_ENV" ADMIN_TOKEN)" ]     || set_env "$BACKEND_ENV" ADMIN_TOKEN "$(gen_secret)"
  [ -n "$(read_env "$BACKEND_ENV" INTERNAL_SECRET)" ] || set_env "$BACKEND_ENV" INTERNAL_SECRET "$(gen_secret)"
  say "Инициализация БД + демо-товары"
  ( cd backend && python -m app.seed )
  say "Фронтенды: npm install"
  ( cd miniapp && npm install )
  ( cd admin && npm install )
  deactivate 2>/dev/null || true
  echo
  ok "Установка завершена. Дальше: ./tgshop.sh config"
  echo
  print_order
}

cfg_mock() {
  echo "── Демо-оплата ──"
  local v
  v="$(read_env "$BACKEND_ENV" PAYMENTS_MOCK)"; [ -n "$v" ] || v=false
  ask v "Демо-оплата (заказ помечается оплаченным сразу, без реальных денег)? on/off" "$([ "$v" = true ] && echo on || echo off)"
  case "$v" in off|false|0) v=false ;; *) v=true ;; esac
  set_env "$BACKEND_ENV" PAYMENTS_MOCK "$v"
}

# Ручной перевод — ЗАПАСНОЙ способ. Robokassa (карты) и TON Connect (крипта)
# настраиваются отдельно; тут только реквизиты для перевода "вручную".
cfg_manual() {
  echo "── Ручной перевод (ЗАПАСНОЙ вариант) ──"
  echo "   Карты автоматом — это Robokassa, крипта автоматом — TON Connect (ниже/��тдельно)."
  echo "   Здесь только реквизиты для перевода вручную. Обычно можно оставить пустым (Enter)."
  local v
  ask v "Реквизиты карты/СБП для ручного перевода (Enter — выкл)" "$(read_env "$BACKEND_ENV" CARD_DETAILS)"
  set_env "$BACKEND_ENV" CARD_DETAILS "$v"
  ask v "Крипто-адрес для РУЧНОГО перевода, без TON Connect (Enter — выкл)" "$(read_env "$BACKEND_ENV" CRYPTO_ADDRESS)"
  set_env "$BACKEND_ENV" CRYPTO_ADDRESS "$v"
  if [ -n "$v" ]; then
    ask v "Сеть этого крипто-адреса (напр. TRC20 / ERC20 / TON)" "$(read_env "$BACKEND_ENV" CRYPTO_NETWORK)"
    set_env "$BACKEND_ENV" CRYPTO_NETWORK "$v"
  else
    set_env "$BACKEND_ENV" CRYPTO_NETWORK ""
  fi
}

cfg_robokassa() {
  echo "── Robokassa (реальный шлюз; для теста — тестовые пароли; пустой логин = выкл) ──"
  local v
  ask v "MerchantLogin (идентификатор магазина)" "$(read_env "$BACKEND_ENV" ROBOKASSA_LOGIN)"
  set_env "$BACKEND_ENV" ROBOKASSA_LOGIN "$v"
  ask v "Пароль #1" "$(read_env "$BACKEND_ENV" ROBOKASSA_PASSWORD1)"
  set_env "$BACKEND_ENV" ROBOKASSA_PASSWORD1 "$v"
  ask v "Пароль #2" "$(read_env "$BACKEND_ENV" ROBOKASSA_PASSWORD2)"
  set_env "$BACKEND_ENV" ROBOKASSA_PASSWORD2 "$v"
  v="$(read_env "$BACKEND_ENV" ROBOKASSA_TEST)"; [ -n "$v" ] || v=true
  ask v "Тестовый режим (IsTest=1)? on/off" "$([ "$v" = false ] && echo off || echo on)"
  case "$v" in off|false|0) v=false ;; *) v=true ;; esac
  set_env "$BACKEND_ENV" ROBOKASSA_TEST "$v"
  ask v "Метод хэша подписи (md5/sha256/...)" "$(read_env "$BACKEND_ENV" ROBOKASSA_HASH || echo md5)"
  set_env "$BACKEND_ENV" ROBOKASSA_HASH "${v:-md5}"
  if [ -n "$(read_env "$BACKEND_ENV" ROBOKASSA_LOGIN)" ]; then
    echo "   В ЛК Robokassa → Технические настройки укажи (адрес бэкенда — твой ngrok/сервер):"
    echo "     Result URL:  <адрес>/api/robokassa/result   (метод GET или POST)"
    echo "     Success URL: <адрес>/api/robokassa/success"
    echo "     Fail URL:    <адрес>/api/robokassa/fail"
  fi
}

cfg_ton() {
  echo "── Криптооплата через TON Connect (сеть TON) ──"
  echo "   ВАЖНО: и TON, и USDT здесь — в сети TON. Оба адреса — это TON-кошельки"
  echo "   (формат EQ… / UQ…). Обычно указывают ОДИН и тот же кошелёк для обоих."
  local ton_addr usdt_addr net key usdt_master trate urate tkey
  # 1) Кошелёк для нативного TON (он же включает всю криптооплату)
  ask ton_addr "Кошелёк TON для приёма TON (Enter — выключить всю криптооплату)" "$(read_env "$BACKEND_ENV" TON_RECEIVE_ADDRESS)"
  set_env "$BACKEND_ENV" TON_RECEIVE_ADDRESS "$ton_addr"
  if [ -z "$ton_addr" ]; then
    set_env "$BACKEND_ENV" TON_USDT_MASTER ""
    set_env "$BACKEND_ENV" TON_USDT_RECEIVE_ADDRESS ""
    echo "   Криптооплата (TON/USDT) отключена."
    return
  fi
  # 2) Сеть
  net="$(read_env "$BACKEND_ENV" TON_NETWORK)"; [ -n "$net" ] || net=mainnet
  ask net "Сеть: mainnet (реальные монеты) / testnet (бесплатно, для обкатки)" "$net"
  case "$net" in testnet) net=testnet ;; *) net=mainnet ;; esac
  set_env "$BACKEND_ENV" TON_NETWORK "$net"
  # 3) toncenter ключ (опционально)
  echo "   toncenter API-ключ — НЕОБЯЗАТЕЛЕН. Это бесплатный ключ с toncenter.com,"
  echo "   он лишь повышает лимит запросов при проверке платежей. Без ключа тоже работает."
  ask key "Ключ toncenter (Enter — без ключа)" "$(read_env "$BACKEND_ENV" TONCENTER_API_KEY)"
  set_env "$BACKEND_ENV" TONCENTER_API_KEY "$key"
  # 4) USDT (в сети TON) — только mainnet
  if [ "$net" = mainnet ]; then
    usdt_master="$(read_env "$BACKEND_ENV" TON_USDT_MASTER)"
    [ -n "$usdt_master" ] || usdt_master="EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
    ask usdt_master "Принимать USDT (в сети TON)? мастер-адрес жетона (Enter — да; '-' — только TON)" "$usdt_master"
    case "$usdt_master" in -|off|no|нет) usdt_master="" ;; esac
    set_env "$BACKEND_ENV" TON_USDT_MASTER "$usdt_master"
    set_env "$BACKEND_ENV" TON_USDT_DECIMALS "6"
    if [ -n "$usdt_master" ]; then
      usdt_addr="$(read_env "$BACKEND_ENV" TON_USDT_RECEIVE_ADDRESS)"; [ -n "$usdt_addr" ] || usdt_addr="$ton_addr"
      echo "   Кошелёк для USDT — тоже адрес в сети TON. Enter = тот же, что для TON."
      ask usdt_addr "Кошелёк TON для приёма USDT (Enter — тот же: $ton_addr)" "$usdt_addr"
      [ -n "$usdt_addr" ] || usdt_addr="$ton_addr"
      set_env "$BACKEND_ENV" TON_USDT_RECEIVE_ADDRESS "$usdt_addr"
      echo "   TonAPI-ключ (tonapi.io) — НЕОБЯЗАТЕЛЕН, но повышает надёжность"
      echo "   АВТОподтверждения USDT-оплаты (без него бывает SSL timeout к tonapi)."
      echo "   Бесплатный ключ — на tonconsole.com."
      ask tkey "Ключ TonAPI для проверки USDT (Enter — без ключа)" "$(read_env "$BACKEND_ENV" TONAPI_API_KEY)"
      set_env "$BACKEND_ENV" TONAPI_API_KEY "$tkey"
    else
      set_env "$BACKEND_ENV" TON_USDT_RECEIVE_ADDRESS ""
    fi
  else
    set_env "$BACKEND_ENV" TON_USDT_MASTER ""
    set_env "$BACKEND_ENV" TON_USDT_RECEIVE_ADDRESS ""
    echo "   (USDT в сети TON есть только в mainnet — в testnet будет только нативный TON)"
  fi
  # 5) Запасные курсы на случай, если CoinGecko недоступен (SSL timeout)
  echo "   Курсы тянутся с CoinGecko. Если к нему нет доступа (ошибка SSL/timeout),"
  echo "   задай запасной курс вручную — он подставится, когда CoinGecko недоступен."
  trate="$(read_env "$BACKEND_ENV" TON_RUB_FALLBACK)"
  ask trate "Запасной курс: ₽ за 1 TON (Enter — только авто)" "$trate"
  set_env "$BACKEND_ENV" TON_RUB_FALLBACK "$trate"
  if [ "$net" = mainnet ] && [ -n "$usdt_master" ]; then
    urate="$(read_env "$BACKEND_ENV" USDT_RUB_FALLBACK)"
    ask urate "Запасной курс: ₽ за 1 USDT (Enter — только авто)" "$urate"
    set_env "$BACKEND_ENV" USDT_RUB_FALLBACK "$urate"
  fi
  echo "   Манифест TON Connect и адрес мини-аппки пропишутся на './tgshop.sh build'."
}

do_config() {
  ensure_env
  say "Настройка. Enter — оставить текущее значение."
  echo "── Telegram ──"
  local v
  ask v "Токен бота (@BotFather)" "$(read_env "$BACKEND_ENV" BOT_TOKEN)"
  set_env "$BACKEND_ENV" BOT_TOKEN "$v"
  ask v "Твой Telegram ID (@userinfobot)" "$(read_env "$BACKEND_ENV" ADMIN_CHAT_ID)"
  set_env "$BACKEND_ENV" ADMIN_CHAT_ID "$v"
  ask v "Пароль админки" "$(read_env "$BACKEND_ENV" ADMIN_PASSWORD || echo admin)"
  set_env "$BACKEND_ENV" ADMIN_PASSWORD "${v:-admin}"
  [ -n "$(read_env "$BACKEND_ENV" ADMIN_TOKEN)" ]     || set_env "$BACKEND_ENV" ADMIN_TOKEN "$(gen_secret)"
  [ -n "$(read_env "$BACKEND_ENV" INTERNAL_SECRET)" ] || set_env "$BACKEND_ENV" INTERNAL_SECRET "$(gen_secret)"
  [ -n "$(read_env "$BACKEND_ENV" BOT_API_URL)" ]     || set_env "$BACKEND_ENV" BOT_API_URL "http://127.0.0.1:8000"
  ok "Основное записано (секреты сгенерированы автоматически)."
  echo
  ask v "Настроить способы оплаты сейчас? y/n" "y"
  case "$v" in y|Y|yes|да|1)
      echo "Порядок: демо → Robokassa (карты) → TON Connect (крипта) → ручной перевод (запас)."
      cfg_mock
      cfg_robokassa
      cfg_ton
      cfg_manual ;;
    *) echo "Пропустил. Позже: ./tgshop.sh pay | robokassa | ton" ;;
  esac
  sync_bot_env
  echo
  ok "Готово. Дальше (в отдельном окне): ./tgshop.sh dev"
}

do_ngrok() {
  if ! command -v ngrok >/dev/null 2>&1; then
    die "ngrok не установлен. Установи: brew install ngrok"
  fi
  say "Запускаю ngrok на 127.0.0.1:${PORT} (оставь это окно открытым)…"
  exec ngrok http "127.0.0.1:${PORT}"
}

do_build() {
  ensure_env
  local url="${1:-}"
  if [ -z "$url" ]; then
    say "Ищу запущенный ngrok…"
    url="$(detect_ngrok_url)"
    [ -n "$url" ] && ok "Нашёл ngrok: $url"
  fi
  [ -n "$url" ] || ask url "URL бэкенда (ngrok, https://...)" ""
  [ -n "$url" ] || die "URL не задан. Сначала './tgshop.sh dev', потом './tgshop.sh ngrok'."
  url="${url%/}"

  # манифест TON Connect должен попасть в сборку -> пишем ДО build
  write_ton_manifest "$url"

  say "Сборка мини-аппки (single-origin, относительный API)"
  ( cd miniapp && printf 'VITE_API_URL=\n' > .env && npm install && npm run build ) \
    || die "Сборка miniapp упала — почини ошибки выше и повтори."
  [ -f miniapp/dist/index.html ] || die "miniapp/dist/index.html не появился после сборки."

  say "Сборка админки (single-origin, base=/admin/)"
  ( cd admin && printf 'VITE_API_URL=\n' > .env && npm install && npm run build ) \
    || die "Сборка admin упала — почини ошибки выше и повтори."
  [ -f admin/dist/index.html ] || die "admin/dist/index.html не появился после сборки."

  set_env "$BACKEND_ENV" API_BASE_URL     "$url"
  set_env "$BACKEND_ENV" MINIAPP_URL      "$url"
  set_env "$BACKEND_ENV" CORS_ORIGINS     "$url"
  set_env "$BACKEND_ENV" TON_MANIFEST_URL "$url/tonconnect-manifest.json"
  sync_bot_env
  set_menu_button "$url"
  echo
  ok "Мини-аппку теперь отдаёт сам бэкенд по адресу: $url"
  ok "Админка (товары/цены/заказы): $url/admin  (пароль = ADMIN_PASSWORD из config)"
  ok "Перезапусти ./tgshop.sh dev (Ctrl+C в ОКНЕ 1 и снова), затем открой бота: /start"
}

do_set_miniapp() {
  ensure_env
  local url="${1:-}"
  if [ -z "$url" ]; then
    say "Обычно адрес прописывает 'build' автоматически. Здесь можно задать вручную"
    say "(например, если хостишь мини-аппку отдельно на Netlify)."
    ask url "Адрес мини-аппки (https://...)" "$(read_env "$BACKEND_ENV" MINIAPP_URL)"
  fi
  [ -n "$url" ] || die "URL не задан"
  url="${url%/}"
  set_env "$BACKEND_ENV" MINIAPP_URL      "$url"
  set_env "$BACKEND_ENV" TON_MANIFEST_URL "$url/tonconnect-manifest.json"
  write_ton_manifest "$url"
  sync_bot_env
  set_menu_button "$url"
  ok "MINIAPP_URL записан в backend/.env и bot/.env: $url"
  ok "Перезапусти ./tgshop.sh dev, чтобы бот увидел кнопку магазина."
}

do_mock() {
  ensure_env
  local val="${1:-}"
  case "$val" in
    on|true|1) val=true ;;
    off|false|0) val=false ;;
    *) ask val "Режим эмуляции оплаты (on/off)" "on"
       case "$val" in off|false|0) val=false ;; *) val=true ;; esac ;;
  esac
  set_env "$BACKEND_ENV" PAYMENTS_MOCK "$val"
  ok "PAYMENTS_MOCK=$val в backend/.env (перезапусти ./tgshop.sh dev)."
}

do_pay() {
  ensure_env
  cfg_mock
  cfg_manual
  ok "Демо и ручной перевод записаны. Robokassa/TON — отдельно: ./tgshop.sh robokassa | ton"
}

do_robokassa() {
  ensure_env
  cfg_robokassa
  ok "Robokassa записана в backend/.env (перезапусти ./tgshop.sh dev)."
}

do_ton() {
  ensure_env
  cfg_ton
  ok "TON записан в backend/.env (перезапусти ./tgshop.sh dev)."
  echo "   Testnet-монеты: @testgiver_ton_bot. USDT (jUSDT) — только mainnet."
}

do_dev() {
  ensure_env
  if [ ! -d .venv ]; then
    die "Нет .venv — сначала: ./tgshop.sh setup"
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  mkdir -p logs

  say "Запуск backend на 127.0.0.1:${PORT} (API + мини-аппка)"
  ( cd backend && exec uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --reload ) > logs/backend.log 2>&1 &
  local back_pid=$!

  echo -n "Жду готовности бэкенда"
  local ready=0 i
  for i in $(seq 1 40); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then ready=1; break; fi
    echo -n "."; sleep 0.5
  done
  echo
  if [ "$ready" = 1 ]; then
    ok "Backend поднялся: $HEALTH_URL"
  else
    warn "Backend не ответил за 20с — лог ниже:"
    tail -n 20 logs/backend.log || true
  fi

  say "Запуск bot"
  ( cd bot && exec python bot.py ) > logs/bot.log 2>&1 &
  local bot_pid=$!

  echo "----------------------------------------"
  echo "Backend → $HEALTH_URL   (PID $back_pid)"
  echo "Bot     → запущен               (PID $bot_pid)"
  echo "Дальше (для телефона): ОКНО 2 './tgshop.sh ngrok' → ОКНО 3 './tgshop.sh build'."
  echo "Ctrl+C — остановить обоих."
  echo "----------------------------------------"

  tail -n +1 -f logs/backend.log logs/bot.log &
  local tail_pid=$!
  trap 'echo; echo "Останавливаю…"; kill '"$back_pid $bot_pid $tail_pid"' 2>/dev/null; exit 0' INT TERM
  wait "$back_pid" "$bot_pid"
}

usage() {
  cat <<'EOF'
TG Shop — управление (single-origin)

Использование: ./tgshop.sh <команда> [аргументы]

  setup                Venv, зависимости backend/bot, npm-модули, БД, демо-товары
  config               Токен/ID/пароль + способы оплаты (Enter оставляет текущее)
  dev                  ОКНО 1: backend (API + мини-аппка) + bot
  ngrok                ОКНО 2: туннель ngrok на :8000
  build [url]          ОКНО 3: собрать мини-аппку, прописать адрес/манифест/кнопку меню
                       (URL берётся у запущенного ngrok, если не передан)
  miniapp [url]        Задать адрес мини-аппки вручную (например, отдельный Netlify)
  mock on|off          Переключить режим эмуляции оплаты
  pay                  Настроить демо/крипту(ручную)/карту
  robokassa            Настроить Robokassa
  ton                  Настроить TON Connect (TON + USDT)
  order                Показать порядок запуска
  help                 Показать эту справку

Быстрый старт (телефон):
  ./tgshop.sh setup && ./tgshop.sh config
  ./tgshop.sh dev            (ОКНО 1)
  ./tgshop.sh ngrok          (ОКНО 2)
  ./tgshop.sh build          (ОКНО 3 — сам возьмёт адрес ngrok)
EOF
}

menu() {
  echo "=============================="
  echo "  TG Shop — управление"
  echo "=============================="
  echo "  1) setup    — установить всё (зависимости, БД)"
  echo "  2) config   — токен/ID/пароль + оплата"
  echo "  3) dev      — backend (API + мини-аппка) + bot (ОКНО 1)"
  echo "  4) ngrok    — туннель (ОКНО 2)"
  echo "  5) build    — собрать мини-аппку + адрес/манифест/кнопку (ОКНО 3)"
  echo "  6) miniapp  — задать адрес мини-аппки вручную"
  echo "  7) mock     — режим эмуляции оплаты"
  echo "  8) pay      — крипта(ручная) и карта/СБП"
  echo "  9) robokassa— ключи Robokassa (реальный шлюз)"
  echo " 10) ton      — TON Connect + USDT (криптооплата)"
  echo " 11) order    — показать порядок запуска"
  echo "  0) выход"
  local choice
  read -r -p "Выбор: " choice
  case "$choice" in
    1) do_setup ;;
    2) do_config ;;
    3) do_dev ;;
    4) do_ngrok ;;
    5) do_build ;;
    6) do_set_miniapp ;;
    7) do_mock ;;
    8) do_pay ;;
    9) do_robokassa ;;
    10) do_ton ;;
    11) print_order ;;
    0) exit 0 ;;
    *) echo "Неизвестный пункт: $choice" ;;
  esac
}

main() {
  local cmd="${1:-menu}"
  shift || true
  case "$cmd" in
    setup)     do_setup "$@" ;;
    config)    do_config "$@" ;;
    dev)       do_dev "$@" ;;
    ngrok)     do_ngrok "$@" ;;
    build)     do_build "$@" ;;
    miniapp)   do_set_miniapp "$@" ;;
    mock)      do_mock "$@" ;;
    pay)       do_pay "$@" ;;
    robokassa) do_robokassa "$@" ;;
    ton)       do_ton "$@" ;;
    order)     print_order ;;
    menu)      menu ;;
    help|-h|--help) usage ;;
    *) warn "Неизвестная команда: $cmd"; usage; exit 1 ;;
  esac
}

main "$@"
