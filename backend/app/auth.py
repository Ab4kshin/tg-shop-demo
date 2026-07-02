"""Валидация Telegram initData (HMAC-SHA256).

Алгоритм (официальный):
  secret_key   = HMAC_SHA256(key="WebAppData", msg=BOT_TOKEN)
  check_hash   = HMAC_SHA256(key=secret_key, msg=data_check_string)
  data_check_string — отсортированные пары key=value через \n (без hash)

user_tg_id берётся ТОЛЬКО из проверенного initData, не из тела запроса.
"""
import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl


def validate_init_data(
    init_data: str, bot_token: str, max_age: int = 86400
) -> Optional[dict]:
    """Вернуть dict пользователя при валидной подписи, иначе None."""
    if not init_data or not bot_token:
        return None
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True, keep_blank_values=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        return None

    # Проверка свежести (защита от переиспользования старой подписи)
    auth_date = pairs.get("auth_date")
    if auth_date and max_age > 0:
        try:
            if time.time() - int(auth_date) > max_age:
                return None
        except ValueError:
            return None

    user_raw = pairs.get("user")
    if not user_raw:
        return None
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None
    if "id" not in user:
        return None
    return user
