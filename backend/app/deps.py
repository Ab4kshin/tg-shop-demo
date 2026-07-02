"""Зависимости FastAPI (Depends)."""
from fastapi import Header, HTTPException

from .auth import validate_init_data
from .config import get_settings


def get_current_user(authorization: str = Header(default="")) -> dict:
    """Извлечь и проверить Telegram initData из заголовка `Authorization: tma <initData>`."""
    settings = get_settings()
    if not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Отсутствует initData")
    init_data = authorization[len("tma ") :]
    user = validate_init_data(init_data, settings.bot_token, settings.initdata_max_age)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверная подпись initData")
    return user


def require_admin(x_admin_token: str = Header(default="")) -> bool:
    """Защита админских эндпоинтов по ADMIN_TOKEN."""
    settings = get_settings()
    if not settings.admin_token or not x_admin_token:
        raise HTTPException(status_code=401, detail="Нет доступа")
    import hmac as _hmac

    if not _hmac.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Нет доступа")
    return True


def full_name(user: dict) -> str:
    parts = [user.get("first_name", ""), user.get("last_name", "")]
    name = " ".join(p for p in parts if p).strip()
    if not name:
        name = user.get("username") or f"id{user.get('id')}"
    return name
