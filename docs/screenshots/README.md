# Скриншоты для README / Screenshots for README

Положи сюда файлы с точно такими именами — они уже вставлены в `README.md` и `README.en.md`.
Place files here using these exact names — they're already referenced from `README.md` and `README.en.md`.

Формат: PNG, ширина ≈ 400–500px для скринов телефона (miniapp-*, bot-*), ≈ 1000–1400px для скринов админки (admin-*).

## Обязательные (используются в README) / Required (used in README)

| Файл | Что снять |
| --- | --- |
| `bot-start.png` | Telegram-чат с ботом: сообщение `/start` с кнопкой «🛍️ Открыть магазин» |
| `miniapp-catalog.png` | Мини-аппка: экран каталога с чипсами категорий и несколькими товарами |
| `miniapp-payment.png` | Мини-аппка: экран инструкций оплаты (лучше всего — крипта, там есть QR) |
| `miniapp-orders.png` | Мини-аппка: вкладка «Мои заказы» со статусами |
| `admin-orders.png` | Админка: таблица заказов со способом оплаты и выбором статуса |
| `admin-products.png` | Админка: таблица товаров + форма добавления/редактирования справа

## Желательные (можно добавить позже) / Optional (nice to have)

| Файл | Что снять |
| --- | --- |
| `miniapp-cart.png` | Мини-аппка: корзина с выбором способа оплаты (до оформления заказа) |
| `admin-stats.png` | Админка: вкладка «Аналитика» (выручка, топ-товары) |
| `admin-login.png` | Админка: экран входа по паролю |
| `landing.png` | Лендинг-страница (`landing/index.html`) в браузере |

## Разрешение / Resolution

Точное разрешение не важно: в README.md и README.en.md ширина отображения задана атрибутом
`width` в теге `<img>`, поэтому GitHub всегда масштабирует их, сохраняя пропорции.
Exact resolution doesn't matter: `README.md`/`README.en.md` fix the display width via the `width`
attribute on `<img>`, so GitHub always scales screenshots while preserving aspect ratio.

⚠️ Важно: **портретные** скриншоты телефона (`bot-*`, `miniapp-*`) и **альбомные** скриншоты админки (`admin-*`) выводятся с РАЗНОЙ шириной: телефонные — узкими превью в ряд (~190px), админка — широким блоком на всю ширину (~760px), чтобы текст/таблицы оставались читаемыми. Если добавишь новый скриншот в README — выбери ширину по аналогии в зависимости от ориентации картинки.
⚠️ Important: **portrait** phone screenshots (`bot-*`, `miniapp-*`) and **landscape** admin screenshots (`admin-*`) use DIFFERENT widths: phone ones are narrow thumbnails in a row (~190px), admin ones are wide full blocks (~760px) so text/tables stay legible. If you add a new screenshot to the README, pick the width by analogy based on its orientation.

Рекомендации / Recommendations:
- Формат / Format: PNG
- Скриншоты телефона (`bot-*`, `miniapp-*`) — просто скриншот экрана как есть (например ≈ 1170×2532 у iPhone) — обрезать не обязательно /
  Phone screenshots — just capture the screen as-is (e.g. ≈ 1170×2532 on iPhone), no cropping required
- Скриншоты админки (`admin-*`) — по возможности обрежь окно браузера до самого интерфейса (без адресной строки/закладок), ширина ≈ 1200–1600px /
  Admin screenshots — crop the browser window to just the app UI (no address bar/bookmarks) if possible, width ≈ 1200–1600px
- Вес файла / File size: желательно до 1 МБ на скриншот, чтобы README быстро грузился / ideally under 1 MB per screenshot so the README loads fast

## Как сделать скриншоты / How to capture

- **Мини-аппка / бот** (`bot-*`, `miniapp-*`): открой бота в Telegram на телефоне, сделай скриншот экрана и обрежь по краям мини-аппки (без статус-бара телефона, если хочется аккуратнее).
- **Админка** (`admin-*`): открой `npm run dev` в папке `admin/` в браузере, сделай скриншот окна браузера (желательно с несколькими тестовыми заказами/товарами для реалистичности).
- Перед съёмкой лучше заполнить базу несколькими тестовыми заказами с разными статусами/способами оплаты — таблицы в README будут выглядеть живее.
