#!/usr/bin/env bash
# TG Shop — единый скрипт управления проектом.
#
# ПОРЯДОК (без «курицы и яйца»):
#   1) ./tgshop.sh setup    — один раз: зависимости + БД
#   2) ./tgshop.sh config   — токен, ID, пароль (адрес ngrok НЕ нужен)
#   3) ./tgshop.sh dev      — backend + bot (ОКНО 1, держать)
#   4) ./tgshop.sh ngrok    — туннель (ОКНО 2, держать)
#   5) ./tgshop.sh build    — сам возьмёт ngrok-адрес, соберёт фронты
#   6) залить miniapp/dist, admin/dist, landing/ на Netlify
#   7) ./tgshop.sh miniapp <netlify-url>   — адрес мини-аппки в .env
#   для оплаты: ./tgshop.sh pay   — тест / крипта / карта-СБП
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PORT=8000
HEALTH_URL="http://127.0.0.1:${PORT}/health"
NGROK_API="http://127.0.0.1:4040/api/tunnels"

# ---------- вспомогательные ----------
ask() {
  local __var="$1" __prompt="$2" __default="${3:-}" __input
  if [ -n "$__default" ]; then
    read -r -p "$__prompt [$__default]: " __input
    __input="${__input:-$__default}"
  else
    read -r -p "$__prompt: " __input
  fi
  printf -v "$__var" '%s' "$__input"
}

gen_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 -c 'import secrets; print(secrets.token_hex(32))'
  fi
}

detect_ngrok_url() {
  curl -s "$NGROK_API" 2>/dev/null | python3 -c 'import sys, json
try:
    data = json.load(sys.stdin)
    urls = [t.get("public_url", "") for t in data.get("tunnels", [])]
    https = [u for u in urls if u.startswith("https")]
    print(https[0] if https else "")
except Exception:
    print("")' 2>/dev/null
}

set_env_var() {
  # set_env_var <file> <KEY> <value>
  local file="$1" key="$2" value="$3"
  [ -f "$file" ] || return 0
  grep -v "^${key}=" "$file" > "${file}.tmp" 2>/dev/null || true
  echo "${key}=${value}" >> "${file}.tmp"
  mv "${file}.tmp" "$file"
}

build_fronts() {
  local url="$1"
  for app in miniapp admin; do
    echo "==> Сборка $app (VITE_API_URL=$url)"
    ( cd "$app" && echo "VITE_API_URL=$url" > .env && npm install && npm run build )
    echo "    → $app/dist готов"
  done
}

print_order() {
  cat <<'MSG'
ПОРЯДОК ЗАПУСКА (локальный тест с телефона):

  1) ./tgshop.sh setup     — один раз: зависимости + БД
  2) ./tgshop.sh config    — токен, ID, пароль (адрес ngrok НЕ нужен!)
  3) ./tgshop.sh dev       — ОКНО 1: backend + bot, держать открытым
  4) ./tgshop.sh ngrok     — ОКНО 2: туннель, держать открытым
  5) ./tgshop.sh build     — ОКНО 3: сам возьмёт ngrok-адрес и соберёт фронты
  6) залей miniapp/dist, admin/dist и папку landing/ на Netlify
  7) ./tgshop.sh miniapp https://твой-адрес.netlify.app
  8) перезапусти ./tgshop.sh dev (Ctrl+C в ОКНЕ 1 и снова)

Способы оплаты:
  • ./tgshop.sh pay   — включить/настроить: тестовая оплата, крипто-адрес, реквизиты карты/СБП

Ключ: СНАЧАЛА dev → ПОТОМ ngrok → ПОТОМ build. Окна dev и ngrok не закрывать.
MSG
}

# ---------- команды ----------
do_setup() {
  echo "==> Python venv + зависимости (backend + bot)"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip >/dev/null
  pip install -r backend/requirements.txt -r bot/requirements.txt
  [ -f backend/.env ] || cp .env.example backend/.env
  [ -f bot/.env ] || cp bot/.env.example bot/.env
  echo "==> Инициализация БД + демо-товары"
  ( cd backend && python -m app.seed )
  echo "==> Фронтенды: npm install"
  ( cd miniapp && npm install )
  ( cd admin && npm install )
  deactivate 2>/dev/null || true
  echo
  echo "✅ Установка завершена."
  echo
  print_order
}

do_config() {
  echo "=== Настройка доступов (.env). Enter — пропустить ==="
  echo "(URL ngrok здесь НЕ нужен — он подхватится позже на шаге build)"
  ask BOT_TOKEN      "Токен бота (@BotFather)"
  ask ADMIN_CHAT_ID  "Твой Telegram ID (@userinfobot)"
  ask ADMIN_PASSWORD "Пароль админки" "admin"

  local admin_token internal_secret
  admin_token="$(gen_secret)"
  internal_secret="$(gen_secret)"

  cat > backend/.env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_CHAT_ID=$ADMIN_CHAT_ID
MINIAPP_URL=
API_BASE_URL=http://localhost:8000
ADMIN_PASSWORD=$ADMIN_PASSWORD
ADMIN_TOKEN=$admin_token
BOT_API_URL=http://127.0.0.1:8000
INTERNAL_SECRET=$internal_secret
DATABASE_PATH=data/shop.sqlite3
CORS_ORIGINS=*
INITDATA_MAX_AGE=86400
PAYMENTS_MOCK=false
CRYPTO_ADDRESS=
CRYPTO_NETWORK=USDT (TRC20)
CARD_DETAILS=
EOF
  cat > bot/.env <<EOF
BOT_TOKEN=$BOT_TOKEN
MINIAPP_URL=
BOT_API_URL=http://127.0.0.1:8000
INTERNAL_SECRET=$internal_secret
EOF
  echo "✅ backend/.env и bot/.env записаны (секреты сгенерированы автоматически)"
  echo "Следующее: ./tgshop.sh dev  (в отдельном окне)"
}

do_ngrok() {
  if ! command -v ngrok >/dev/null 2>&1; then
    echo "ngrok не установлен. Установи: brew install ngrok"
    return 1
  fi
  echo "Запускаю ngrok на 127.0.0.1:${PORT} (оставь это окно открытым)..."
  exec ngrok http "127.0.0.1:${PORT}"
}

do_build() {
  local url="${1:-}"
  if [ -z "$url" ]; then
    echo "URL не задан — ищу запущенный ngrok..."
    url="$(detect_ngrok_url)"
    if [ -n "$url" ]; then
      echo "→ Нашёл ngrok: $url"
    else
      echo "ngrok не найден. Сначала запусти './tgshop.sh dev', потом './tgshop.sh ngrok'."
      ask url "Или введи URL бэкенда вручную"
    fi
  fi
  if [ -z "$url" ]; then
    echo "❌ URL не задан"
    return 1
  fi
  build_fronts "$url"
  set_env_var backend/.env API_BASE_URL "$url"
  echo
  echo "✅ Фронты собраны, API_BASE_URL в backend/.env обновлён."
  echo "   → перезалей miniapp/dist и admin/dist на Netlify"
}

do_set_miniapp() {
  local url="${1:-}"
  if [ -z "$url" ]; then
    ask url "Адрес мини-аппки на Netlify (https://...)"
  fi
  if [ -z "$url" ]; then
    echo "❌ URL не задан"
    return 1
  fi
  set_env_var backend/.env MINIAPP_URL "$url"
  set_env_var bot/.env MINIAPP_URL "$url"
  echo "✅ MINIAPP_URL записан в backend/.env и bot/.env."
  echo "   → перезапусти ./tgshop.sh dev, чтобы бот увидел кнопку магазина."
}

do_mock() {
  local val="${1:-}"
  case "$val" in
    on|true|1) val=true ;;
    off|false|0) val=false ;;
    *) ask val "Режим эмуляции оплаты (on/off)" "on"
       case "$val" in off|false|0) val=false ;; *) val=true ;; esac ;;
  esac
  set_env_var backend/.env PAYMENTS_MOCK "$val"
  echo "✅ PAYMENTS_MOCK=$val в backend/.env (перезапусти ./tgshop.sh dev)."
}

do_pay() {
  echo "=== Способы оплаты (Enter — пропустить/выключить) ==="
  local mock crypto cryptonet card
  ask mock "Тестовая оплата (мгновенно)? on/off" "on"
  case "$mock" in off|false|0) mock=false ;; *) mock=true ;; esac
  ask crypto "Крипто-адрес кошелька USDT (пусто — выкл)"
  ask cryptonet "Сеть криптовалюты" "USDT (TRC20)"
  ask card "Реквизиты карты/СБП для перевода (пусто — выкл)"
  set_env_var backend/.env PAYMENTS_MOCK "$mock"
  set_env_var backend/.env CRYPTO_ADDRESS "$crypto"
  set_env_var backend/.env CRYPTO_NETWORK "$cryptonet"
  set_env_var backend/.env CARD_DETAILS "$card"
  echo "✅ Способы оплаты записаны в backend/.env (перезапусти ./tgshop.sh dev)."
}

do_dev() {
  if [ ! -d .venv ]; then
    echo "Нет .venv — сначала: ./tgshop.sh setup"
    return 1
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  mkdir -p logs

  echo "==> Запуск backend на 127.0.0.1:${PORT}"
  ( cd backend && exec uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --reload ) > logs/backend.log 2>&1 &
  local back_pid=$!

  echo -n "Жду готовности бэкенда"
  local ok=0 i
  for i in $(seq 1 40); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then ok=1; break; fi
    echo -n "."
    sleep 0.5
  done
  echo
  if [ "$ok" = 1 ]; then
    echo "✅ Backend поднялся: $HEALTH_URL"
  else
    echo "⚠️  Backend не ответил за 20с — лог ниже:"
    tail -n 20 logs/backend.log || true
  fi

  echo "==> Запуск bot"
  ( cd bot && exec python bot.py ) > logs/bot.log 2>&1 &
  local bot_pid=$!

  echo "----------------------------------------"
  echo "Backend → $HEALTH_URL   (PID $back_pid)"
  echo "Bot     → работает             (PID $bot_pid)"
  echo "Дальше (для телефона): ОКНО 2 './tgshop.sh ngrok' → ОКНО 3 './tgshop.sh build'."
  echo "Ctrl+C — остановить обоих."
  echo "----------------------------------------"

  tail -n +1 -f logs/backend.log logs/bot.log &
  local tail_pid=$!
  trap 'echo; echo "Останавливаю…"; kill '"$back_pid $bot_pid $tail_pid"' 2>/dev/null; exit 0' INT TERM
  wait "$back_pid" "$bot_pid"
}

menu() {
  echo "=============================="
  echo "  TG Shop — управление"
  echo "=============================="
  echo "  1) setup   — установить всё (зависимости, БД)"
  echo "  2) config  — токен/ID/пароль в .env"
  echo "  3) dev     — backend + bot (ОКНО 1)"
  echo "  4) ngrok   — туннель (ОКНО 2)"
  echo "  5) build   — собрать фронты под ngrok"
  echo "  6) miniapp — вписать адрес Netlify мини-аппки"
  echo "  7) mock    — режим эмуляции оплаты"
  echo "  8) pay     — крипта и карта/СБП (реквизиты)"
  echo "  9) order   — показать порядок запуска"
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
    9) print_order ;;
    0) exit 0 ;;
    *) echo "Неизвестный выбор" ;;
  esac
}

cmd="${1:-menu}"
case "$cmd" in
  setup) do_setup ;;
  config|configure) do_config ;;
  ngrok) do_ngrok ;;
  build) shift; do_build "${1:-}" ;;
  miniapp) shift; do_set_miniapp "${1:-}" ;;
  mock) shift; do_mock "${1:-}" ;;
  pay) do_pay ;;
  dev|start) do_dev ;;
  order|help) print_order ;;
  menu|"") menu ;;
  *) echo "Использование: ./tgshop.sh [setup|config|dev|ngrok|build|miniapp|mock|pay|order]"; exit 1 ;;
esac
